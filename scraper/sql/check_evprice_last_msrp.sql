With latest_timestamp as (
    SELECT 
        brand_name,
        model_name,
        MAX(create_timestamp) AS latest_timestamp
    FROM
        $$DB_PRICE_TABLE$$
    WHERE 
        brand_name = '$$brand_name$$' AND
        model_name = '$$model_name$$'
    GROUP BY 1, 2
)

SELECT
    msrp
FROM 
    $$DB_PRICE_TABLE$$ as ep INNER JOIN 
    latest_timestamp as lt ON 
        ep.brand_name = lt.brand_name AND
        ep.model_name = lt.model_name AND 
        ep.create_timestamp = lt.latest_timestamp
