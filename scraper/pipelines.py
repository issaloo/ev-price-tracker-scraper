import hashlib
from datetime import date

import psycopg2
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

        str_lc_fields = ["brand_name", "model_name", "car_type"]
        for field in str_lc_fields:
            adapter[field] = adapter[field].lower()
        return item


class InsertDataPipeline:
    
    """Insert msrp data into table."""
    
    def __init__(self):
        self.hostname = "evpricetrackerdb.internal"
        self.username = "postgres"
        self.password = ""  # TODO: do not save here
        self.database = "ev_price"
        self.connection = psycopg2.connect(host=self.hostname, 
                                           user=self.username, 
                                           password=self.password, 
                                           dbname=self.database)
        self.cur = self.connection.cursor()

    def replace_query_params(self, query: str, params: dict):
        """Replace query with parameters."""
        for key, value in params.items():
            query = query.replace(f"$${key}$$", value)
        return query

    def read_sql_file(self, query_file_path: str, params: dict | None = None):
        """Read sql from file path."""
        with open(query_file_path, "r") as f:
            query = f.read()
        if params:
            return self.replace_query_params(query, params)
        return query

    def process_item(self, item, spider):
        """
        Process an item to insert msrp data into table.

        Args:
        ----
            item (scrapy.Item): The item to be processed.
            spider (scrapy.Spider): The spider that generated the item.

        Returns:
        -------
            scrapy.Item: The processed item if all required fields are present.
        """
        # create table if not exists
        create_query = self.read_sql_file("sql/create_evprice.sql")
        self.cur.execute(create_query)

        adapter = ItemAdapter(item)

        # check table is empty
        check_query = self.read_sql_file("sql/check_evprice_empty.sql")
        self.cur.execute(check_query)
        record_count = self.cur.fetchone()

        # check if msrp changed
        if record_count > 0:
            check_fields = ["brand_name", "model_name"]
            check_dict = {field: adapter.get(field) for field in check_fields}
            check_query = self.read_sql_file("sql/check_evprice_last_msrp.sql", check_dict)
            self.cur.execute(check_query)
            last_msrp = self.cur.fetchone()
            if last_msrp == adapter.get("msrp"):
                spider.logger.warn("MSRP did not change for item.")
                return None

        # insert data into table
        insert_dict = adapter.asdict()
        insert_query = self.read_sql_file("sql/insert_evprice_new_msrp.sql", insert_dict)
        self.cur.execute(insert_query)
