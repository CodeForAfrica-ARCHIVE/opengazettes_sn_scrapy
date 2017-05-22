# -*- coding: utf-8 -*-
import os.path
import logging
from scrapy.http import Request
from scrapy.utils.request import referer_str
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.files import FileException
from scrapy.utils.misc import md5sum

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

logger = logging.getLogger(__name__)

from collections import defaultdict

class FSFilesStore(object):

    def __init__(self, basedir):
        if '://' in basedir:
            basedir = basedir.split('://', 1)[1]
        self.basedir = basedir
        self._mkdir(self.basedir)
        self.created_directories = defaultdict(set)

    def persist_file(self, path, buf, info, meta=None, headers=None):
        absolute_path = self._get_filesystem_path(path)
        self._mkdir(os.path.dirname(absolute_path), info)
        with open(absolute_path, 'rb') as f:
            f.write(buf.getvalue())
        print('I have reache write buaaaaaaaaaaaaaananananananananananananananananananananananananananananananaan')
    def stat_file(self, path, info):
        absolute_path = self._get_filesystem_path(path)
        try:
            last_modified = os.path.getmtime(absolute_path)
        except os.error:
            return {}

        with open(absolute_path, 'rb') as f:
            checksum = md5sum(f)

        return {'last_modified': last_modified, 'checksum': checksum}

    def _get_filesystem_path(self, path):
        path_comps = path.split('/')
        return os.path.join(self.basedir, *path_comps)

    def _mkdir(self, dirname, domain=None):
        seen = self.created_directories[domain] if domain else set()
        if dirname not in seen:
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            seen.add(dirname)

class OpengazettesSnFilesPipeline(FilesPipeline):

    loop = []

    def media_downloaded(self, response, request, info):
        print('yeeh i have been called, woohoo: ', response.url)
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
        print('status is as follows', status )
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )
        self.inc_stats(info.spider, status)

        try:
            print('Ihave reached try')
            path = self.file_path(request, response=response, info=info)
            print('this the path ', path)
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
        print('this is the item for filename: ', item['filename'])
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
                request.meta['gazette_month'],
                filename, media_ext)

    def file_downloaded(self, response, request, info):
        path = self.file_path(request, response=response, info=info)
        content = self.modify_response(response)
        self.loop.append(content)
        if len(self.loop) == request.meta['file_urls_len']:
            cont = ''
            for item in self.loop:
                cont += item.decode("utf-8") + '\n'

            buf = BytesIO(bytes(cont, 'utf-8'))
            checksum = md5sum(buf)
            buf.seek(0)
            self.store.persist_file(path, buf, info)
            self.loop = []
            print('file saved: ', path)
            return checksum
        print('length of files is ========> ', len(self.loop))
        print('length of file_urls is ========> ', request.meta['file_urls_len'])
        return None

    def modify_response(self, response):
        print('type of response body', type(response.body))
        article_contents = response.xpath('//*[@id="explorei"]/div[2]').extract()
        content = ''
        for article_content in article_contents:
            content += article_content + '\n'

        return bytes(content, 'utf-8')


