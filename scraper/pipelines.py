import hashlib
from datetime import date

import psycopg2
import scrapy
from google.cloud import secretmanager
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


# TODO: install google cloud
def access_secret_version(secret_id, version_id="latest"):
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(name=name)

    # Return the decoded payload.
    return response.payload.data.decode("UTF-8")


class DropMissingPipeline:

    """Ensure no fields are missing."""

    def process_item(self, item: scrapy.Item, spider: scrapy.spider):
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

    def process_item(self, item: scrapy.Item, spider: scrapy.spider):
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

    def process_item(self, item: scrapy.Item, spider: scrapy.spider):
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
        """
        Attributes
        ----------
            hostname (str): The hostname or IP address of the PostgreSQL server.
            username (str): The username for connecting to the PostgreSQL database.
            password (str): The password for connecting to the PostgreSQL database.
            database (str): The name of the PostgreSQL database to connect to.
            port (int): The port number to use for the database connection.
            connection: A connection object to the PostgreSQL database.
            cursor: A cursor object for executing SQL queries.
            base_sql_path (str): The base path for SQL script files used in the EV Price Tracker (default: "scraper/sql").

        """
        self.hostname = "localhost"
        self.username = "postgres"
        self.password = ""  # TODO: do not save here
        self.database = "evpricetracker"
        self.port = 5432
        self.connection = psycopg2.connect(
            host=self.hostname, user=self.username, password=self.password, dbname=self.database, port=self.port
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        self.base_sql_path = "scraper/sql"

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
        create_query = self.read_sql_file(f"{self.base_sql_path}/create_evprice.sql")
        self.cursor.execute(create_query)

        adapter = ItemAdapter(item)

        # check if data available for specific brand name and model name
        check_fields = ["brand_name", "model_name"]
        check_dict = {field: adapter.get(field) for field in check_fields}
        check_query = self.read_sql_file(f"{self.base_sql_path}/check_evprice_empty.sql", check_dict)
        self.cursor.execute(check_query)
        record_count = self.cursor.fetchone()[0]

        # check if msrp changed
        if record_count > 0:
            check_query = self.read_sql_file(f"{self.base_sql_path}/check_evprice_last_msrp.sql", check_dict)
            self.cursor.execute(check_query)
            last_msrp = float(self.cursor.fetchone()[0])
            if last_msrp == float(adapter.get("msrp")):
                spider.logger.info("MSRP did not change for item.")
                return None

        # insert data into table
        insert_dict = adapter.asdict()
        insert_query = self.read_sql_file(f"{self.base_sql_path}/insert_evprice_new_msrp.sql", insert_dict)
        self.cursor.execute(insert_query)
