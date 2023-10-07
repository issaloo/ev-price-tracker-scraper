SELECT 
    count(*) AS total_records
FROM 
    ev_price
WHERE 
    brand_name = '$$brand_name$$' AND
    model_name = '$$model_name$$'