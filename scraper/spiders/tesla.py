import scrapy
import re

# from scrapy.selector


class TeslaSpider(scrapy.Spider):
    name = "teslascraper"

    def __init__(self):
        self.lc = "abcdefghijklmnopqrstuvwxyz"
        self.uc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def start_requests(self):
        base_url = "http://www.tesla.com"
        model_list = ["model s", "model 3", "model x", "model y"]  # TODO: make this dynamic
        for model in model_list:
            url = f"{base_url}/{model.replace(' ', '')}"
            yield scrapy.Request(url=url, callback=self.parse, meta={"model": model})

    def parse(self, response):
        model = response.meta.get("model")
        
        # get dollar value
        xpath_dollar_str = f'//p[contains(translate(@class, "{self.uc}", "{self.lc}"), "disclaimer")]/text()'
        text_list = response.xpath(xpath_dollar_str).getall()
        price = [text.replace(",", "") for text in text_list if "$" in text][0]
        price = float(re.search(r"\b(?<=\$)\d+\b", price).group(0))
    
        # get image source
        xpath_img_str = (f'//picture[contains(translate(@data-alt, "{self.uc}", "{self.lc}"), "{model}") ' 
                            f'and contains(translate(@data-alt, "{self.uc}", "{self.lc}"), "side view")]/'
                            f'@data-iesrc[contains(translate(., "{self.uc}", "{self.lc}"), "order")]')
        img_src = response.xpath(xpath_img_str).get()

        # yield data
        result = {"brand": "tesla", 
                  "model": model,
                  "price": price,
                  "image_src": img_src}
        yield result
