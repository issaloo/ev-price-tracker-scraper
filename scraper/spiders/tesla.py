import scrapy

# from scrapy.selector


class TeslaSpider(scrapy.Spider):
    name = "teslascraper"

    def __init__(self):
        self.lc = "abcdefghijklmnopqrstuvwxyz"
        self.uc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def start_requests(self):
        base_url = "http://www.tesla.com"
        model_list = ["models", "model3", "modelx", "modely"]  # TODO: make this dynamic
        for model in model_list:
            url = f"{base_url}/{model}"
            yield scrapy.Request(url=url, callback=self.parse, meta={"model": model})

    def parse(self, response):
        text_list = response.xpath(
            f'//p[contains(translate(@class, {self.uc}, {self.lc}), "disclaimer")]/text()'
        ).getall()
        dollar_list = ["$" in text.replace(",", "") for text in text_list]
        if len(dollar_list) == 1:
            dollar_list[0]
            # TODO: extract dollar value using regex
        else:
            ValueError("Need single text extracted for dollar value.")
        result = {"brand": "tesla", "model": self.meta.model}  # TODO: add meta
        yield result
