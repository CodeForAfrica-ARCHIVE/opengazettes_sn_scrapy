# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OpengazettesSnItem(scrapy.Item):
    # define the fields for your item here like:
    gazette_link = scrapy.Field()
    publication_date = scrapy.Field()
    gazette_number = scrapy.Field()
    files = scrapy.Field()
    special_issue = scrapy.Field()
    file_urls = scrapy.Field()
    filename = scrapy.Field()
    gazette_title = scrapy.Field()
    gazette_name = scrapy.Field()
