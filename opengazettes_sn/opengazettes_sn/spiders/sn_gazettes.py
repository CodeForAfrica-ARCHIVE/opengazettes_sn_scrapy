import scrapy
import os
import re
from datetime import datetime

from ..items import OpengazettesNgItem


class GazettesSpider(scrapy.Spider):
    name = "ng_gazettes"
    allowed_domains = ["www.jo.gouv.sn"]

    def start_requests(self):
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
        years_list = len(response.xpath('//*[@id="explorei"]/ul[1]/li').extract())
        year_link = self.get_year_link(response, years_list, year)


        # access the year_link
        url = 'http://www.jo.gouv.sn/' + year_link
        request = scrapy.Request(url, callback=self.get_year_gazettes)
        yield request

    def get_year_link(self, response, years_list, year):
        for year_num in range(1, years_list):
            got_year = response.xpath('//*[@id="explorei"]/ul[1]/li[{}]/font/a/text()'.format(year_num)).extract_first()
            if got_year == year:
                return response.xpath('//*[@id="explorei"]/ul[1]/li[{}]/font/a[@class="menu"]/@href'.format(year_num)).extract_first()

    def get_year_gazettes(self, response):
        # initialize gazette_meta
        gazette_meta = OpengazettesNgItem()

        articles = len(response.xpath('//*[@id="explorei"]/ul[1]/li').extract())
        for article in range(1, articles + 1):
            gazette_meta['gazette_name'] = response.xpath(
                '//*[@id="explorei"]/ul[1]/li[{}]/font/a/text()'.format(article)).extract_first()
            gazette_meta['gazette_link'] = response.xpath(
                '//*[@id="explorei"]/ul[1]/li[{}]/font/a[@class="menu"]/@href'.format(article)).extract_first()
            url = 'http://www.jo.gouv.sn/' + gazette_meta['gazette_link']
            request = scrapy.Request(url, self.get_gazette_article_links)
            request.meta['gazette_meta'] = gazette_meta
            yield request

    def get_gazette_article_links(self, response):
        article_links = len(response.xpath('//*[@id="explorei"]/ul/li').extract())
        item = response.meta['gazette_meta']
        for article_link in range(1, article_links + 1):
            link = response.xpath(
                '//*[@id="explorei"]/ul/li[{}]/a[@class="menu"]/@href'.format(article_link)).extract_first()
            url = 'http://www.jo.gouv.sn/' + link
            request = scrapy.Request(url, callback=self.download_article)
            request.meta['gazette_meta'] = item
            yield request

    def download_article(self, response):
        articles = response.xpath('//*[@id="explorei"]/div[2]').extract()
        gazette_meta =  response.meta['gazette_meta']
        gazette_name = gazette_meta['gazette_name']

        item = self.create_gazette_meta(gazette_meta, gazette_name)

        file_name = './gazettes/{}/{}/{}.html'.format(
            item['gazette_year'],
            item['gazette_month'],
            item['filename']
        )
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'a') as file:
            for article in articles:
                file.write(article)
        print('file => {} has been written'.format(file_name))
        yield item

    def create_gazette_meta(self, gazette_meta, gazette_name):
        gazette_name = self.process_gazette_name(gazette_name)
        gazette_number, gazette_day, gazette_year = tuple(re.findall(r'\d+', gazette_name))
        gazette_month = re.findall(r'\b[A-Za-z]+\b', gazette_name)[-1]

        gazette_meta['gazette_number'] = gazette_number
        gazette_meta['gazette_year'] = gazette_year
        gazette_meta['gazette_month'] = gazette_month
        gazette_meta['gazette_day'] = gazette_day
        # gazette_meta['week_day'] = week_day
        gazette_title, gazette_file_name = self.create_gazette_name_title(gazette_meta)

        gazette_meta['gazette_title'] = gazette_title
        gazette_meta['filename'] = gazette_file_name

        return gazette_meta

    def process_gazette_name(self, gazette_name):
        gazette_name = gazette_name.lower()
        import locale
        locale.setlocale(locale.LC_ALL, 'fr_FR')

        import calendar

        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']

        # days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for month in months:
            m_index = months.index(month) + 1
            if calendar.month_name[m_index].lower() in gazette_name:
                gazette_name = gazette_name.replace(calendar.month_name[m_index], month)
                return gazette_name

    def create_gazette_name_title(self, gazette_meta):
        filename = 'opengazettes-sn-no-{}-dated-{}-{}-{}'.format(
            gazette_meta['gazette_number'],
            gazette_meta['gazette_day'],
            gazette_meta['gazette_month'],
            gazette_meta['gazette_year']
        )

        title = 'Senegal Government Gazette No.{} Dated {} {} {}'.format(
            gazette_meta['gazette_number'],
            gazette_meta['gazette_day'],
            gazette_meta['gazette_month'],
            gazette_meta['gazette_year']
        )
        return  filename, title
