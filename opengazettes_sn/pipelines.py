# -*- coding: utf-8 -*-
import logging
from scrapy.http import Request
from scrapy.utils.request import referer_str
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.files import FileException
from scrapy.utils.misc import md5sum

from unidecode import unidecode
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

logger = logging.getLogger(__name__)


class OpengazettesSnFilesPipeline(FilesPipeline):

    loop = []

    def media_downloaded(self, response, request, info):
        referer = referer_str(request)

        if response.status != 200:
            logger.warning(
                'File (code: %(status)s): Error downloading file from '
                '%(request)s referred in <%(referer)s>',
                {'status': response.status,
                 'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('download-error')

        if not response.body:
            logger.warning(
                'File (empty-content): Empty file from %(request)s referred '
                'in <%(referer)s>: no-content',
                {'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('empty-content')

        status = 'cached' if 'cached' in response.flags else 'downloaded'
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )
        self.inc_stats(info.spider, status)

        try:
            path = self.file_path(request, response=response, info=info)
            checksum = self.file_downloaded(response, request, info)
        except FileException as exc:
            logger.warning(
                'File (error): Error processing file from %(request)s '
                'referred in <%(referer)s>: %(errormsg)s',
                {'request': request, 'referer': referer, 'errormsg': str(exc)},
                extra={'spider': info.spider}, exc_info=True
            )
            raise
        except Exception as exc:
            logger.error(
                'File (unknown-error): Error processing file from %(request)s '
                'referred in <%(referer)s>',
                {'request': request, 'referer': referer},
                exc_info=True, extra={'spider': info.spider}
            )
            raise FileException(str(exc))

        return {'url': request.url, 'path': path, 'checksum': checksum }

    def get_media_requests(self, item, info):
        return [Request(x, meta={'filename': item["filename"],
                'gazette_year': item['gazette_year'], 'gazette_month': item['gazette_month'],
                                 'file_urls_len': len(item['file_urls'])})
                for x in item.get(self.files_urls_field, [])]

    def file_path(self, request, response=None, info=None):
        # start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('FilesPipeline.file_key(url) method is deprecated,\
            please use file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        # end of deprecation warning block

        # Now using file name passed in the meta data
        filename = request.meta['filename']
        media_ext = '.html'
        return '%s/%s/%s%s' % \
            (request.meta['gazette_year'],
                self.get_month_number(request.meta['gazette_month']),
                filename, media_ext)

    def file_downloaded(self, response, request, info):
        path = self.file_path(request, response=response, info=info)
        content = self.modify_response(response)
        self.loop.append(content)
        if len(self.loop) == request.meta['file_urls_len']:
            cont = ''
            for item in self.loop:
                cont += item + '\n'

            buf = BytesIO(cont.encode('ascii', 'ignore'))
            checksum = md5sum(buf)
            buf.seek(0)
            self.store.persist_file(path, buf, info)
            self.loop = []
            return checksum
        return None

    def modify_response(self, response):
        article_contents = response.xpath('//*[@id="explorei"]/div[2]').extract()
        content = ''
        for article_content in article_contents:
            content += article_content + '\n'

        return content

    def get_month_number(self, month):
        months_fr = ['janvier', 'fevrier', 'mars', 'avril',
                     'mai', 'juin','juillet', 'aout',
                     'septembre', 'octobre', 'novembre', 'decembre']
        p_month = unidecode(month.strip()).lower()
        month_number = str(months_fr.index(p_month) + 1)
        if len(month_number) == 1:
            return '0' + month_number
        return month_number