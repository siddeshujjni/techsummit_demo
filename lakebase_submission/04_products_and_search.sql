-- Milestone 2.4 — Products table + Lakebase Search (full-text + vector)
-- Run against: databricks_postgres on meridian-bank/production

-- STEP 0: Enable required extensions (vector MUST come before lakebase_vector)
CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector prerequisite
CREATE EXTENSION IF NOT EXISTS lakebase_vector CASCADE;
CREATE EXTENSION IF NOT EXISTS lakebase_text;

CREATE TABLE meridian_bank.products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    segment TEXT NOT NULL,
    rate_apy DOUBLE PRECISION,
    min_balance_usd DOUBLE PRECISION,
    description TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

INSERT INTO meridian_bank.products (product_id, product_name, product_type, segment, rate_apy, min_balance_usd, description) VALUES
('PROD-DEP-2001', '18-Month Certificate of Deposit', 'CD', 'deposit', 0.0325, 1000.0, '18-month term CD for savers locking in a fixed rate; penalty on early withdrawal. For rate-focused deposit customers.'),
('PROD-DEP-2002', 'High-Yield Savings', 'Savings', 'deposit', 0.0290, 0.0, 'Liquid high-yield savings account, tiered rate on higher balances. For customers holding cash who want yield with access.'),
('PROD-DEP-2003', '12-Month Certificate of Deposit', 'CD', 'deposit', 0.0300, 1000.0, '12-month term CD, shorter lock for rate-focused savers. Alternative to the 18-month CD.'),
('PROD-INV-3001', 'Wealth Advisory Account', 'Advisory', 'investment', NULL, 100000.0, 'Managed wealth advisory account with a dedicated advisor. For affluent and private-tier customers with investable assets; a cross-sell for high-balance depositors.'),
('PROD-CRD-4001', 'Premier Rewards Credit Card', 'Card', 'lending', NULL, 0.0, 'Premium rewards credit card, travel + cashback perks. For mass-affluent and above with strong relationship tenure; a cross-sell for depositors without a card.'),
('PROD-LN-5001', 'Home Equity Line of Credit', 'HELOC', 'lending', 0.0725, 0.0, 'Revolving home-equity line of credit. For homeowners with equity; a lending cross-sell for established relationship customers.'),
('PROD-DEP-2010', 'Everyday Checking', 'Checking', 'deposit', 0.0010, 0.0, 'No-frills everyday checking account with direct deposit and bill pay. The core relationship anchor product.'),
('PROD-DEP-2011', 'Money Market Account', 'Savings', 'deposit', 0.0250, 2500.0, 'Money market account, tiered yield with limited monthly transactions. For savers wanting a blend of yield and access.'),
('PROD-LN-5002', '30-Year Fixed Mortgage', 'Mortgage', 'lending', 0.0665, 0.0, '30-year fixed-rate home mortgage. For homebuyers; a long-tenure relationship product.'),
('PROD-LN-5003', 'Auto Loan', 'Auto', 'lending', 0.0620, 0.0, 'Fixed-rate auto loan for new and used vehicles. Broad-eligibility lending product.'),
('PROD-INV-3002', 'Self-Directed Brokerage', 'Brokerage', 'investment', NULL, 0.0, 'Self-directed online brokerage account. For customers who want to invest without an advisor; a cross-sell for affluent depositors.');

-- Add tsvector search column + GIN index (full-text search)
ALTER TABLE meridian_bank.products
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
    to_tsvector('english',
        coalesce(product_name, '') || ' ' ||
        coalesce(description, '') || ' ' ||
        coalesce(product_type, '') || ' ' ||
        coalesce(segment, '')
    )
) STORED;

CREATE INDEX products_search_gin_idx
ON meridian_bank.products USING GIN (search_vector);

-- Lakebase Search: BM25 index for hybrid ranking
CREATE INDEX products_bm25_idx ON meridian_bank.products
USING lakebase_bm25 (product_name, description, product_type, segment);

-- Example: Full-text search query
SELECT product_id, product_name, ts_rank(search_vector, query) AS rank
FROM meridian_bank.products, plainto_tsquery('english', 'high yield savings') AS query
WHERE search_vector @@ query
ORDER BY rank DESC LIMIT 5;
