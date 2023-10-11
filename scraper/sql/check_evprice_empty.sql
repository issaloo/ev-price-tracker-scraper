SELECT 
    count(*) AS total_records
FROM 
    $$DB_PRICE_TABLE$$
WHERE 
    brand_name = '$$brand_name$$' AND
    model_name = '$$model_name$$'