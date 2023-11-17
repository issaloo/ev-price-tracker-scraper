import re
from datetime import datetime, timezone

import scrapy

from ..items import EvItem


class RivianSpider(scrapy.Spider):

    """Rivian spider to scrape for car details."""

    name = "rivian_scraper"

    def __init__(self):
        """
        Attributes
        ----------
            lc (str): A string containing lowercase alphabetic characters 'abcdefghijklmnopqrstuvwxyz' for xpath translate
            uc (str): A string containing uppercase alphabetic characters 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' for xpath translate
            base_url (str): The base URL for Rivian's website.
        """
        self.lc = "abcdefghijklmnopqrstuvwxyz"
        self.uc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.base_url = "http://www.rivian.com"

    def start_requests(self):
        """
        Generate initial requests for scraping Rivian's electric vehicle information.

        This method prepares and yields a series of Scrapy requests to fetch data for Rivian electric vehicle models.

        Returns
        -------
            Iterable[scrapy.Request]: A sequence of Scrapy requests, each specifying a URL to scrape and providing
            metadata including the model name and car type
        """
        model_list = [
            ("r1s", "suv"),
            ("r1t", "truck"),
        ]  # TODO: make this dynamic
        for model_name, car_type in model_list:
            url = f"{self.base_url}/{model_name.replace(' ', '')}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"model_name": model_name, "car_type": car_type, "model_url": url},
            )

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
        ev_item["brand_name"] = "rivian"

        model_name = response.meta.get("model_name")
        car_type = response.meta.get("car_type")
        model_url = response.meta.get("model_url")

        ev_item["model_name"] = model_name
        ev_item["car_type"] = car_type
        ev_item["model_url"] = model_url
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
        xpath_dollar_str = (
            f'(//div[contains(translate(@data-section-gtm, "{self.uc}", "{self.lc}"), "starting price")]//'
            'h5[contains(., "$")]/text())[last()]'
        )
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
        xpath_img_str = f'(//img[contains(@src, "{model_name.upper()}") and contains(@src, "f_auto,q_auto")]/@src)[1]'
        img_src = response.xpath(xpath_img_str).getall()[0]
        return img_src
