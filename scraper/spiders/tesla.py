import re
from datetime import datetime, timezone

import scrapy

from ..items import EvItem


class TeslaSpider(scrapy.Spider):

    """Tesla spider to scrape for car details."""

    name = "tesla_scraper"

    def __init__(self):
        """
        Attributes
        ----------
            lc (str): A string containing lowercase alphabetic characters 'abcdefghijklmnopqrstuvwxyz' for xpath translate
            uc (str): A string containing uppercase alphabetic characters 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' for xpath translate
            base_url (str): The base URL for Tesla's website.
        """
        self.lc = "abcdefghijklmnopqrstuvwxyz"
        self.uc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.base_url = "http://www.tesla.com"

    def start_requests(self):
        """
        Generate initial requests for scraping Tesla's electric vehicle information.

        This method prepares and yields a series of Scrapy requests to fetch data for Tesla electric vehicle models.

        Returns
        -------
            Iterable[scrapy.Request]: A sequence of Scrapy requests, each specifying a URL to scrape and providing
            metadata including the model name and car type
        """
        model_list = [
            ("model s", "sedan"),
            ("model 3", "sedan"),
            ("model x", "suv"),
            ("model y", "suv"),
        ]  # TODO: make this dynamic
        for model_name, car_type in model_list:
            url = f"{self.base_url}/{model_name.replace(' ', '')}"
            yield scrapy.Request(url=url, callback=self.parse, meta={"model_name": model_name, "car_type": car_type})

    def parse(self, response):
        """
        Parse electric vehicle data from given url.

        Args:
        ----
            response (scrapy.http.Response): The response object containing the webpage content.

        Returns:
        -------
            generator: Yields EvItem objects with the extracted information.
        """
        ev_item = EvItem()
        ev_item["brand_name"] = "tesla"

        model_name = response.meta.get("model_name")
        car_type = response.meta.get("car_type")

        ev_item["model_name"] = model_name
        ev_item["car_type"] = car_type
        ev_item["msrp"] = self.extract_msrp(response)
        ev_item["image_src"] = self.extract_image_src(response, model_name)
        ev_item["create_timestamp"] = datetime.now(timezone.utc)

        yield ev_item

    def extract_msrp(self, response):
        """
        Extract the MSRP (Manufacturer's Suggested Retail Price) from the response.

        Args:
        ----
            response (scrapy.http.Response): The response object containing the webpage content.

        Returns:
        -------
            str or None: The extracted MSRP value as a string or None if not found.
        """
        xpath_dollar_str = f'//p[contains(translate(@class, "{self.uc}", "{self.lc}"), "disclaimer")]/text()'
        text_list = response.xpath(xpath_dollar_str).getall()
        price = [text.replace(",", "") for text in text_list if "$" in text][0]
        if price:
            return re.search(r"\b(?<=\$)\d+\b", price).group(0)
        return None

    def extract_image_src(self, response, model_name):
        """
        Extract the image source URL for a given model name from the response.

        Args:
        ----
            response (scrapy.http.Response): The response object containing the webpage content.
            model_name (str): The name of the electric vehicle model.

        Returns:
        -------
            str or None: The extracted image source URL as a string or None if not found.
        """
        xpath_img_str = (
            f'//picture[contains(translate(@data-alt, "{self.uc}", "{self.lc}"), "{model_name}")]/'
            f'@data-iesrc[contains(translate(., "{self.uc}", "{self.lc}"), "order")]'
        )
        return response.xpath(xpath_img_str).get()
