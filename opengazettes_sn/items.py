# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OpengazettesSnItem(scrapy.Item):
    # define the fields for your item here like:
    gazette_link = scrapy.Field() # link to the gazette on http://www.jo.gouv.sn/spip.php
    publication_date = scrapy.Field() # date the gazette is published
    gazette_number = scrapy.Field()
    file_urls = scrapy.Field() # path to the file
    gazette_links = scrapy.Field() # I am not sure what this is
    filename = scrapy.Field() # the new filename
    gazette_title = scrapy.Field() # title of the gazette
    gazette_day = scrapy.Field()
    gazette_month = scrapy.Field()
    gazette_year = scrapy.Field()
    gazette_name = scrapy.Field()
