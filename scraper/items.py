from scrapy.item import Item, Field
from datetime import datetime


class EvItem(Item):
    brand_name = Field()
    model_name = Field()
    image_src = Field()
    msrp = Field()
    timestamp = Field()
