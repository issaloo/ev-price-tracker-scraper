import re

import scrapy

from ..items import EvItem
from datetime import datetime, timezone

class TeslaSpider(scrapy.Spider):
    name = "tesla_scraper"

    def __init__(self):
        """""" # TODO: add
        self.lc = "abcdefghijklmnopqrstuvwxyz"
        self.uc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def start_requests(self):
        """""" # TODO: add
        base_url = "http://www.tesla.com"
        model_list = ["model s", "model 3", "model x", "model y"]  # TODO: make this dynamic
        for model_name in model_list:
            url = f"{base_url}/{model_name.replace(' ', '')}"
            yield scrapy.Request(url=url, callback=self.parse, meta={"model_name": model_name})

    def parse(self, response):
        """""" # TODO: add stuff
        ev_item = EvItem()

        ev_item["brand_name"] = "tesla"
        model_name = response.meta.get("model_name")
        ev_item["model_name"] = model_name

        xpath_dollar_str = f'//p[contains(translate(@class, "{self.uc}", "{self.lc}"), "disclaimer")]/text()'
        text_list = response.xpath(xpath_dollar_str).getall()
        price = [text.replace(",", "") for text in text_list if "$" in text][0]
        ev_item["msrp"] = re.search(r"\b(?<=\$)\d+\b", price).group(0)

        xpath_img_str = (
            f'//picture[contains(translate(@data-alt, "{self.uc}", "{self.lc}"), "{model_name}")]/'
            f'@data-iesrc[contains(translate(., "{self.uc}", "{self.lc}"), "order")]'
        )
        print(response.xpath(xpath_img_str).get())
        ev_item["image_src"] = response.xpath(xpath_img_str).get()
        ev_item["timestamp"] = datetime.now(timezone.utc).isoformat() # TODO: update this
        
        yield ev_item # TODO: maybe don't use
