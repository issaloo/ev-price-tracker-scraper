import hashlib
import os
from datetime import date

import psycopg2
import scrapy
from dotenv import load_dotenv
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

################################
# Set Up Environment Variables #
################################

# Using .env, load DB variables
load_dotenv()
BASE_SQL_PATH = "scraper/sql"
DB_HOSTNAME = os.getenv("DB_HOSTNAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_PORT = os.getenv("DB_PORT")
DB_PRICE_TABLE = os.getenv("DB_PRICE_TABLE")

# Using GCF & SM, access secret through mounting as volume
secret_location = "/postgres/secret"
with open(secret_location) as f:
    secret_payload = f.readlines()[0]

# Establish a connection to the PostgreSQL DB
try:
    connection = psycopg2.connect(
        host=DB_HOSTNAME,
        user=DB_USERNAME,
        password=secret_payload,
        dbname=DB_DATABASE,
        port=DB_PORT,
    )
    connection.autocommit = True
    cursor = connection.cursor()
except Exception as e:
    print(f"Error connecting to the database: {e}")


########################
# Initialize Pipelines #
########################


class DropMissingPipeline:

    """Ensure no fields are missing."""

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
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

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
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

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
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

    def read_sql_file(self, query_file_path: str, params: dict | None = None):
        """Read sql from file path.

        Args:
        ----
            query_file_path (str):
        Returns:


        """
        with open(query_file_path, "r") as f:
            query = f.read()
        if params:
            for key, value in params.items():
                query = query.replace(f"$${key}$$", str(value))
        return query

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
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
        create_dict = {"DB_PRICE_TABLE": DB_PRICE_TABLE}
        create_query = self.read_sql_file(f"{BASE_SQL_PATH}/create_evprice.sql", create_dict)
        cursor.execute(create_query)

        adapter = ItemAdapter(item)

        # check if data available for specific brand name and model name
        check_fields = ["brand_name", "model_name"]
        check_dict = {field: adapter.get(field) for field in check_fields}
        check_dict["DB_PRICE_TABLE"] = DB_PRICE_TABLE
        check_query = self.read_sql_file(f"{BASE_SQL_PATH}/check_evprice_empty.sql", check_dict)
        cursor.execute(check_query)
        record_count = cursor.fetchone()[0]

        # check if msrp changed
        if record_count > 0:
            check_query = self.read_sql_file(f"{BASE_SQL_PATH}/check_evprice_last_msrp.sql", check_dict)
            cursor.execute(check_query)
            last_msrp = float(cursor.fetchone()[0])
            if last_msrp == float(adapter.get("msrp")):
                spider.logger.info("MSRP did not change for item.")
                return None

        # insert data into table
        insert_dict = adapter.asdict()
        insert_dict["DB_PRICE_TABLE"] = DB_PRICE_TABLE
        insert_query = self.read_sql_file(f"{BASE_SQL_PATH}/insert_evprice_new_msrp.sql", insert_dict)
        cursor.execute(insert_query)
