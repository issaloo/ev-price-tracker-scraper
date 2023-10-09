INSERT INTO $$DB_PRICE_TABLE$$ (
    ev_id, 
    brand_name, 
    model_name, 
    car_type, 
    image_src, 
    msrp, 
    create_timestamp)
VALUES (
    '$$ev_id$$',
    '$$brand_name$$', 
    '$$model_name$$', 
    '$$car_type$$', 
    '$$image_src$$', 
    $$msrp$$, 
    '$$create_timestamp$$')