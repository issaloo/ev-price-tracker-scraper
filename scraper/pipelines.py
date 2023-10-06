import hashlib
from datetime import date

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DropMissingPipeline:

    """Ensure no fields are missing."""

    def process_item(self, item, spider):
        """
        Process an item to ensure no missing fields.

        Args:
        ----
            item (scrapy.Item): The item to be processed.
            spider (scrapy.Spider): The spider that generated the item.

        Returns:
        -------
            scrapy.Item: The processed item if all required fields are present.

        Raises:
        ------
            DropItem: If any of the required fields are missing, a DropItem exception is raised.
        """
        adapter = ItemAdapter(item)

        required_fields = ["image_src", "msrp"]
        missing_fields = [field for field in required_fields if not adapter.get(field)]
        if missing_fields:
            raise DropItem(f"Missing required fields: {', '.join(missing_fields)}")
        return item


class CreateRecordIdPipeline:

    """Create unique record ID."""

    def process_item(self, item, spider):
        """
        Process an item to create a unique record ID.

        Args:
        ----
            item (scrapy.Item): The item to be processed.
            spider (scrapy.Spider): The spider that generated the item.

        Returns:
        -------
            scrapy.Item: The processed item with the 'ev_id' field containing the unique record ID.
        """
        adapter = ItemAdapter(item)

        input_fields = ["brand_name", "model_name"]
        input_value = "_".join([adapter.get(field) for field in input_fields])
        hash_input = f"{input_value}_{date.today().isoformat()}"
        adapter["ev_id"] = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        return item


class CleanDataPipeline:

    """Clean and normalize data."""

    def process_item(self, item, spider):
        """
        Process an item to clean data.

        Args:
        ----
            item (scrapy.Item): The item to be processed.
            spider (scrapy.Spider): The spider that generated the item.

        Returns:
        -------
            scrapy.Item: The processed item with cleaned and normalized data.
        """
        adapter = ItemAdapter(item)

        # Set data types for non-string values
        float_fields = ["msrp"]
        for field in float_fields:
            adapter[field] = float(adapter[field])

        # Lowercase string values
        str_lc_fields = ["brand_name", "model_name", "car_type"]
        for field in str_lc_fields:
            adapter[field]
        return item
