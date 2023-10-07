CREATE TABLE IF NOT EXISTS ev_price (
    ev_id VARCHAR(32) PRIMARY KEY, 
    brand_name VARCHAR(50) NOT NULL, 
    model_name VARCHAR(50) NOT NULL, 
    car_type VARCHAR(50) NOT NULL, 
    image_src VARCHAR(255) NOT NULL, 
    msrp float(24) NOT NULL, 
    create_timestamp TIMESTAMPTZ NOT NULL)