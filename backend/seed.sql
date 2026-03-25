-- ============================================================
-- AlloyDB / PostgreSQL Schema for SME Data Copilot
-- Run this script to create tables and seed sample data
-- ============================================================

DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS businesses CASCADE;

-- Businesses
CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100),
    founded_year INT,
    employee_count INT,
    annual_revenue DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    business_id INT REFERENCES businesses(id),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    sku VARCHAR(50) UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    warehouse_location VARCHAR(200),
    quantity INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    last_restocked TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    business_id INT REFERENCES businesses(id),
    product_id INT REFERENCES products(id),
    transaction_type VARCHAR(50), -- 'sale', 'purchase', 'return'
    quantity INT,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    customer_country VARCHAR(100),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Businesses
INSERT INTO businesses (name, industry, country, city, founded_year, employee_count, annual_revenue, status) VALUES
('TechNova Solutions', 'Technology', 'India', 'Bangalore', 2018, 45, 1250000.00, 'active'),
('GreenLeaf Exports', 'Agriculture', 'Vietnam', 'Ho Chi Minh City', 2015, 120, 3400000.00, 'active'),
('Pacific Trade Co', 'Retail', 'Singapore', 'Singapore', 2020, 25, 890000.00, 'active'),
('Sakura Electronics', 'Electronics', 'Japan', 'Tokyo', 2012, 200, 8500000.00, 'active'),
('Dragon Manufacturing', 'Manufacturing', 'China', 'Shenzhen', 2016, 350, 12000000.00, 'active'),
('Spice Route Foods', 'Food & Beverage', 'India', 'Mumbai', 2019, 60, 2100000.00, 'active'),
('K-Beauty Global', 'Cosmetics', 'South Korea', 'Seoul', 2017, 80, 4500000.00, 'active'),
('Island Fresh Produce', 'Agriculture', 'Philippines', 'Manila', 2014, 90, 1800000.00, 'active'),
('Thai Silk Traders', 'Textiles', 'Thailand', 'Bangkok', 2013, 150, 5600000.00, 'active'),
('Oceanic Logistics', 'Logistics', 'Australia', 'Sydney', 2011, 300, 15000000.00, 'active')
ON CONFLICT DO NOTHING;

-- Products
INSERT INTO products (business_id, name, category, price, cost, sku, status) VALUES
(1, 'Cloud Analytics Platform', 'Software', 299.99, 50.00, 'TN-SW-001', 'active'),
(1, 'AI Chatbot Module', 'Software', 149.99, 30.00, 'TN-SW-002', 'active'),
(2, 'Organic Rice (Premium)', 'Grains', 12.50, 4.00, 'GL-GR-001', 'active'),
(2, 'Vietnamese Coffee Beans', 'Beverages', 18.99, 6.50, 'GL-BV-001', 'active'),
(3, 'Smart Home Hub', 'Electronics', 89.99, 35.00, 'PT-EL-001', 'active'),
(3, 'Wireless Earbuds Pro', 'Electronics', 59.99, 20.00, 'PT-EL-002', 'active'),
(4, 'OLED Display Panel', 'Components', 450.00, 200.00, 'SE-CP-001', 'active'),
(4, 'Micro Controller Unit', 'Components', 15.00, 5.00, 'SE-CP-002', 'active'),
(5, 'Steel Fasteners Kit', 'Hardware', 25.00, 8.00, 'DM-HW-001', 'active'),
(5, 'Aluminum Enclosure', 'Hardware', 75.00, 30.00, 'DM-HW-002', 'active'),
(6, 'Masala Spice Box', 'Spices', 8.99, 2.50, 'SR-SP-001', 'active'),
(6, 'Organic Turmeric Powder', 'Spices', 6.49, 1.80, 'SR-SP-002', 'active'),
(7, 'Hydrating Face Serum', 'Skincare', 34.99, 8.00, 'KB-SK-001', 'active'),
(7, 'Vitamin C Moisturizer', 'Skincare', 28.99, 7.00, 'KB-SK-002', 'active'),
(8, 'Fresh Mango (Export)', 'Fruits', 5.99, 1.50, 'IF-FR-001', 'active'),
(8, 'Coconut Oil (Virgin)', 'Oils', 11.99, 3.50, 'IF-OL-001', 'active'),
(9, 'Thai Silk Scarf', 'Accessories', 45.00, 15.00, 'TS-AC-001', 'active'),
(9, 'Handwoven Fabric Roll', 'Textiles', 120.00, 40.00, 'TS-TX-001', 'active'),
(10, 'Express Shipping Service', 'Services', 35.00, 20.00, 'OL-SV-001', 'active'),
(10, 'Warehouse Storage (Monthly)', 'Services', 200.00, 100.00, 'OL-SV-002', 'active')
ON CONFLICT DO NOTHING;

-- Inventory
INSERT INTO inventory (product_id, warehouse_location, quantity, reorder_level, last_restocked) VALUES
(1, 'Cloud (Digital)', 9999, 0, '2025-01-15'),
(2, 'Cloud (Digital)', 9999, 0, '2025-01-15'),
(3, 'HCMC Warehouse A', 5000, 500, '2025-02-10'),
(4, 'HCMC Warehouse A', 3000, 300, '2025-02-10'),
(5, 'Singapore Hub', 800, 100, '2025-01-20'),
(6, 'Singapore Hub', 1500, 200, '2025-01-20'),
(7, 'Tokyo Factory', 200, 50, '2025-03-01'),
(8, 'Tokyo Factory', 10000, 1000, '2025-03-01'),
(9, 'Shenzhen Plant', 25000, 5000, '2025-02-15'),
(10, 'Shenzhen Plant', 3000, 500, '2025-02-15'),
(11, 'Mumbai Warehouse', 8000, 1000, '2025-01-25'),
(12, 'Mumbai Warehouse', 6000, 800, '2025-01-25'),
(13, 'Seoul Distribution', 4000, 500, '2025-02-20'),
(14, 'Seoul Distribution', 3500, 400, '2025-02-20'),
(15, 'Manila Cold Storage', 2000, 300, '2025-03-05'),
(16, 'Manila Processing', 1500, 200, '2025-03-05'),
(17, 'Bangkok Workshop', 600, 100, '2025-02-28'),
(18, 'Bangkok Workshop', 150, 30, '2025-02-28'),
(19, 'Sydney Depot', 9999, 0, '2025-01-10'),
(20, 'Sydney Depot', 50, 10, '2025-01-10')
ON CONFLICT DO NOTHING;

-- Transactions
INSERT INTO transactions (business_id, product_id, transaction_type, quantity, unit_price, total_amount, currency, customer_country, transaction_date) VALUES
(1, 1, 'sale', 5, 299.99, 1499.95, 'USD', 'India', '2025-01-15 10:30:00'),
(1, 1, 'sale', 3, 299.99, 899.97, 'USD', 'Singapore', '2025-01-20 14:00:00'),
(1, 2, 'sale', 10, 149.99, 1499.90, 'USD', 'Japan', '2025-02-05 09:15:00'),
(2, 3, 'sale', 500, 12.50, 6250.00, 'USD', 'Japan', '2025-01-18 08:00:00'),
(2, 4, 'sale', 200, 18.99, 3798.00, 'USD', 'Australia', '2025-02-10 11:30:00'),
(2, 3, 'sale', 1000, 12.50, 12500.00, 'USD', 'South Korea', '2025-02-20 07:45:00'),
(3, 5, 'sale', 50, 89.99, 4499.50, 'SGD', 'Singapore', '2025-01-22 16:00:00'),
(3, 6, 'sale', 100, 59.99, 5999.00, 'SGD', 'Malaysia', '2025-02-01 13:20:00'),
(4, 7, 'sale', 20, 450.00, 9000.00, 'JPY', 'China', '2025-01-25 10:00:00'),
(4, 8, 'sale', 5000, 15.00, 75000.00, 'JPY', 'Vietnam', '2025-02-15 08:30:00'),
(5, 9, 'sale', 10000, 25.00, 250000.00, 'CNY', 'India', '2025-01-30 09:00:00'),
(5, 10, 'sale', 500, 75.00, 37500.00, 'CNY', 'Thailand', '2025-02-18 14:45:00'),
(6, 11, 'sale', 2000, 8.99, 17980.00, 'INR', 'United States', '2025-02-01 10:00:00'),
(6, 12, 'sale', 3000, 6.49, 19470.00, 'INR', 'United Kingdom', '2025-02-12 11:00:00'),
(7, 13, 'sale', 500, 34.99, 17495.00, 'KRW', 'Japan', '2025-01-28 15:30:00'),
(7, 14, 'sale', 800, 28.99, 23192.00, 'KRW', 'China', '2025-02-22 09:45:00'),
(8, 15, 'sale', 1000, 5.99, 5990.00, 'PHP', 'Japan', '2025-02-05 07:00:00'),
(8, 16, 'sale', 300, 11.99, 3597.00, 'PHP', 'Australia', '2025-02-25 12:15:00'),
(9, 17, 'sale', 100, 45.00, 4500.00, 'THB', 'United States', '2025-01-15 16:00:00'),
(9, 18, 'sale', 20, 120.00, 2400.00, 'THB', 'France', '2025-03-01 10:30:00'),
(10, 19, 'sale', 200, 35.00, 7000.00, 'AUD', 'New Zealand', '2025-02-08 08:00:00'),
(10, 20, 'sale', 15, 200.00, 3000.00, 'AUD', 'Singapore', '2025-02-28 14:00:00'),
(1, 1, 'sale', 8, 299.99, 2399.92, 'USD', 'Australia', '2025-03-01 10:00:00'),
(2, 4, 'sale', 500, 18.99, 9495.00, 'USD', 'India', '2025-03-05 09:30:00'),
(5, 9, 'sale', 15000, 25.00, 375000.00, 'CNY', 'Japan', '2025-03-10 08:00:00'),
(3, 5, 'return', 5, 89.99, -449.95, 'SGD', 'Singapore', '2025-02-15 10:00:00'),
(7, 13, 'return', 20, 34.99, -699.80, 'KRW', 'Japan', '2025-03-05 11:00:00'),
(4, 7, 'sale', 30, 450.00, 13500.00, 'JPY', 'South Korea', '2025-03-12 14:00:00'),
(6, 11, 'sale', 5000, 8.99, 44950.00, 'INR', 'Canada', '2025-03-15 10:30:00'),
(9, 17, 'sale', 200, 45.00, 9000.00, 'THB', 'Germany', '2025-03-18 16:00:00')
ON CONFLICT DO NOTHING;
