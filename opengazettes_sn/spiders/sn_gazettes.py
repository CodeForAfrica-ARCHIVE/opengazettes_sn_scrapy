from datetime import datetime
import errno
import os
import re
import scrapy
from unidecode import unidecode

from ..items import OpengazettesSnItem


class GazettesSpider(scrapy.Spider):
    name = "sn_gazettes"
    allowed_domains = ["www.jo.gouv.sn"]

    def start_requests(self):
        # trying to catch filename for special Gazettes with no gazette dates
        self.cached_file_name = ''

        url = 'http://www.jo.gouv.sn/spip.php?rubrique2'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Get the year to be crawled from the arguments
        # The year is passed like this: scrapy crawl gazettes -a year=2017
        # Default to current year if year not passed in
        try:
            year = self.year
        except AttributeError:
            year = datetime.now().strftime('%Y')

        # select list with all years
        years_list = len(response.xpath(
            '//*[@id="explorei"]/ul[1]/li').extract()) + 1

        year_link = self.get_year_link(response, years_list, year)


        # access the year_link
        url = 'http://www.jo.gouv.sn/' + year_link
        request = scrapy.Request(url, callback=self.get_year_gazettes)
        yield request

    def get_year_link(self, response, years_list, year):
        for year_num in range(1, years_list):
            got_year = response.xpath(
                '//*[@id="explorei"]/ul[1]/li[{}]/font/a/text()'
                    .format(year_num)).extract_first()
            if got_year == year:
                return response.xpath('//*[@id="explorei"]/ul[1]/li[{}]/\
                font/a[@class="menu"]/@href'.format(year_num)).extract_first()

    def get_year_gazettes(self, response):
        articles = len(response.xpath(
            '//*[@id="explorei"]/ul[1]/li').extract())

        for article in range(articles, 0, -1):
            # initialize gazette_meta
            gazette_meta = OpengazettesSnItem()

            gazette_meta['gazette_name'] = response.xpath(
                '//*[@id="explorei"]/ul[1]/li[{}]/font/a/text()'
                    .format(article)).extract_first()

            gazette_meta['gazette_link'] = response.xpath(
                '//*[@id="explorei"]/ul[1]/li[{}]/font/a[@class="menu"]/\
                @href'.format(article)).extract_first()

            item = self.create_gazette_meta(gazette_meta,
                                            gazette_meta['gazette_name'])
            url = 'http://www.jo.gouv.sn/' + gazette_meta['gazette_link']
            request = scrapy.Request(url, self.get_gazette_article_links)
            request.meta['gazette_meta'] = item
            yield request

    def get_gazette_article_links(self, response):
        article_links = len(response.xpath(
            '//*[@id="explorei"]/ul/li').extract())

        item = response.meta['gazette_meta']
        gazette_links = []
        for article_link in range(1, article_links + 1):
            link = response.xpath(
                '//*[@id="explorei"]/ul/li[{}]/a[@class="menu"]/@href'
                    .format(article_link)).extract_first()
            url = 'http://www.jo.gouv.sn/' + link
            gazette_links.append(url)
        item['file_urls'] = gazette_links

        yield item

    def create_gazette_meta(self, gazette_meta, gazette_name):
        # remove french accents from words and lowercase them
        gazette_name = unidecode(gazette_name.lower())

        gazette_name, gazette_meta = self.check_special(
                                    gazette_name, gazette_meta)
        gazette_name = self.cache_filename(gazette_name)

        gazette_number, gazette_day, gazette_year = tuple(
            re.findall(r'\d+', gazette_name))

        gazette_month = re.findall(r'\b[A-Za-z]+\b', gazette_name)[-1]

        gazette_meta['gazette_number'] = gazette_number
        gazette_meta['gazette_year'] = gazette_year
        gazette_meta['gazette_month'] = gazette_month
        gazette_meta['gazette_day'] = gazette_day

        gazette_file_name, gazette_title = (
            self.create_gazette_name_title(gazette_meta))

        gazette_meta['gazette_title'] = gazette_title
        gazette_meta['filename'] = gazette_file_name

        return gazette_meta

    def get_month_number(self, month):
        months_fr = ['janvier', 'fevrier', 'mars', 'avril',
                     'mai', 'juin','juillet', 'aout',
                     'septembre', 'octobre', 'novembre', 'decembre']
        p_month = unidecode(month.strip()).lower()
        for month in months_fr:
            # sometimes the month name on http://www.jo.gouv.sn/spip.php
            # are misspelt, hence the startswith check
            if month == p_month or month.startswith(p_month[:4]):
                month_number = str(months_fr.index(month) + 1)

        if len(month_number) == 1:
            return '0' + month_number
        return month_number

    def create_gazette_name_title(self, gazette_meta):
        if gazette_meta['special_issue'] == True:
            gazette_no = str(gazette_meta['gazette_number']) + ' Special'
        else: gazette_no = gazette_meta['gazette_number']

        filename = 'opengazettes-sn-no-{}-dated-{}-{}-{}'.format(
            gazette_no.lower(),
            gazette_meta['gazette_day'],
            gazette_meta['gazette_month'],
            gazette_meta['gazette_year']
        )

        title = 'Senegal Government Gazette No.{} Dated {} {} {}'.format(
            gazette_no,
            gazette_meta['gazette_day'],
            gazette_meta['gazette_month'].capitalize(),
            gazette_meta['gazette_year']
        )
        return  filename, title

    def check_special(self, gazette_name, gazette_meta):
        gazette_meta['special_issue'] = False
        special_chars = ['- 2', 'n - s', 'ns' ]
        for char in special_chars:
            if char in gazette_name:
                gazette_name = gazette_name.replace(char, '')
                gazette_meta['special_issue'] = True
            if 'special' in gazette_name:
                gazette_meta['special_issue'] = True
        return gazette_name, gazette_meta

    def cache_filename(self, filename):
        if len (filename.split()) < 4:
            filename = self.cached_file_name
        else:
            self.cached_file_name = filename
        return  filename


