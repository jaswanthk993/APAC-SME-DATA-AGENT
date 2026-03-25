-- 1️⃣ Basic — Total Revenue by Industry
SELECT 
  b.industry AS category,
  SUM(t.total_amount) AS total_revenue,
  COUNT(t.id) AS total_transactions
FROM transactions t
JOIN businesses b ON b.id = t.business_id
GROUP BY b.industry
ORDER BY total_revenue DESC;

-- 2️⃣ With Business Count + Avg Per Business
SELECT
  b.industry AS category,
  COUNT(DISTINCT b.id)          AS total_businesses,
  COUNT(t.id)                   AS total_transactions,
  SUM(t.total_amount)           AS total_revenue,
  ROUND(AVG(t.total_amount), 2) AS avg_transaction,
  ROUND(
    SUM(t.total_amount) /
    NULLIF(COUNT(DISTINCT b.id), 0), 2
  )                             AS revenue_per_business
FROM transactions t
JOIN businesses b ON b.id = t.business_id
GROUP BY b.industry
ORDER BY total_revenue DESC;

-- 5️⃣ Monthly Revenue Trend by Industry
SELECT
  b.industry AS category,
  DATE_TRUNC('month', t.transaction_date) AS month,
  SUM(t.total_amount)                     AS monthly_revenue,
  COUNT(t.id)                             AS transactions
FROM transactions t
JOIN businesses b ON b.id = t.business_id
GROUP BY b.industry, DATE_TRUNC('month', t.transaction_date)
ORDER BY b.industry, month;

-- 7️⃣ Top Business Per Industry
SELECT DISTINCT ON (b.industry)
  b.industry AS category,
  b.name AS business_name,
  b.city,
  SUM(t.total_amount) OVER (
    PARTITION BY b.id
  )                   AS business_revenue,
  SUM(t.total_amount) OVER (
    PARTITION BY b.industry
  )                   AS category_total
FROM transactions t
JOIN businesses b ON b.id = t.business_id
ORDER BY b.industry,
         business_revenue DESC;

-- 🔟 Full Dashboard Query — Everything in One
WITH rev AS (
  SELECT
    b.id,
    b.industry AS category,
    b.name AS business_name,
    b.city,
    SUM(t.total_amount)           AS revenue,
    COUNT(t.id)                   AS txn_count,
    COUNT(DISTINCT t.product_id)  AS unique_products,
    MAX(t.transaction_date)       AS last_sale_date
  FROM transactions t
  JOIN businesses b ON b.id = t.business_id
  GROUP BY b.id, b.industry, b.name, b.city
),
cat_summary AS (
  SELECT
    category,
    COUNT(*)                      AS businesses,
    SUM(revenue)                  AS cat_revenue,
    SUM(txn_count)                AS cat_txns,
    MAX(revenue)                  AS top_biz_revenue,
    ROUND(AVG(revenue), 0)        AS avg_biz_revenue
  FROM rev
  GROUP BY category
),
grand AS (
  SELECT SUM(cat_revenue) AS total
  FROM cat_summary
)
SELECT
  cs.category,
  cs.businesses,
  cs.cat_txns                     AS transactions,
  cs.cat_revenue                  AS total_revenue,
  cs.avg_biz_revenue              AS avg_per_business,
  ROUND(
    cs.cat_revenue * 100.0 /
    g.total, 1
  )                               AS revenue_share_pct,
  (
    SELECT r2.business_name
    FROM rev r2
    WHERE r2.category = cs.category
    ORDER BY r2.revenue DESC
    LIMIT 1
  )                               AS top_business,
  (
    SELECT r2.city
    FROM rev r2
    WHERE r2.category = cs.category
    ORDER BY r2.revenue DESC
    LIMIT 1
  )                               AS top_city
FROM cat_summary cs
CROSS JOIN grand g
ORDER BY cs.cat_revenue DESC;
