SELECT
  id,
  name
FROM raw.raw_customers
LIMIT 1000;

SELECT
  MIN(CAST(ordered_at AS date)) AS earliest_order,
  MAX(CAST(ordered_at AS date)) AS latest_order,
  MAX(CAST(ordered_at AS date)) - MIN(CAST(ordered_at AS date)) AS span_days
FROM raw.raw_orders;
