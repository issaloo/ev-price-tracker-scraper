import hashlib
import json
import os
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv
from google.cloud import secretmanager
from google.oauth2 import service_account

# using .env, load DB variables
load_dotenv()
BASE_SQL_PATH = "scraper/sql"
DB_HOSTNAME = os.getenv("DB_HOSTNAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_PORT = os.getenv("DB_PORT")
DB_PRICE_TABLE = os.getenv("DB_PRICE_TABLE")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_SECRET_2_ID = os.getenv("GCP_SECRET_2_ID")
GCP_VERSION_ID = os.getenv("GCP_VERSION_ID")

# load creds and get payload
with open("credentials.json", "r") as f:
    credentials = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(credentials)
    client = secretmanager.SecretManagerServiceClient(credentials=credentials)
load_dotenv()

name = f"projects/{GCP_PROJECT_ID}/secrets/{GCP_SECRET_2_ID}/versions/{GCP_VERSION_ID}"
response = client.access_secret_version(name=name)
secret_payload = response.payload.data.decode("UTF-8")

# establish a connection to the PostgreSQL DB
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

# TODO: UPDATE STATIC VALUES
insert_dict = {}
insert_dict["DB_PRICE_TABLE"] = DB_PRICE_TABLE  # TODO: Set to Staging if necessary
insert_dict["brand_name"] = "INSERT_BRAND_NAME"
insert_dict["model_name"] = "INSERT_MODEL_NAME"
insert_dict["car_type"] = "INSERT_CAR_TYPE"
insert_dict["image_src"] = "INSERT_IMAGE_SRC"
insert_dict["model_url"] = "INSERT_URL"
input_fields = ["brand_name", "model_name"]
input_value = "_".join([insert_dict[field] for field in input_fields])

# TODO: UPDATE LIST OF DATES AND PRICES
date_price_list = [
    ("YYYY-MM-DD", "INSERT_PRICE"),
]
for datev, price in date_price_list:
    hash_input = f"{input_value}_{datev}"
    insert_dict["ev_id"] = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
    date_value = datetime.strptime(datev, "%Y-%m-%d")
    insert_date = datetime.now(timezone.utc).replace(year=date_value.year, month=date_value.month, day=date_value.day)
    insert_dict["create_timestamp"] = insert_date
    insert_dict["msrp"] = price
    with open(f"{BASE_SQL_PATH}/insert_evprice_new_msrp.sql", "r") as f:
        query = f.read()
    if insert_dict:
        for key, value in insert_dict.items():
            query = query.replace(f"$${key}$$", str(value))
    cursor.execute(query)
