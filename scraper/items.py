from scrapy.item import Field, Item


class EvItem(Item):

    """
    Data about electric vehicles (EVs).

    Attributes
    ----------
        ev_id: unique id for line of data
        brand_name: The brand or manufacturer name of the electric vehicle
        model_name: The model name of the electric vehicle
        image_src: The source URL of an image representing the electric vehicle
        msrp: The Manufacturer's Suggested Retail Price (MSRP) of the electric vehicle
        timestamp: The timestamp indicating when the data was scraped
    """

    ev_id = Field()
    brand_name = Field()
    model_name = Field()
    car_type = Field()
    image_src = Field()
    msrp = Field()
    create_timestamp = Field()
