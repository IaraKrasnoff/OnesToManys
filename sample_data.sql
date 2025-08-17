-- OnesToManys Project Sample Data
-- Created for Phase 1 requirement: SQL file with synthetic data
-- Simplified: 3 orders with 3 items each

-- Insert sample orders (3 orders)
INSERT INTO orders (customer_id, order_date, total_amount) VALUES
(101, '2025-08-15', 85.47),
(102, '2025-08-16', 142.50),
(103, '2025-08-17', 97.25);

-- Insert sample order items (3 items per order = 9 total items)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total) VALUES
-- Order 1 items (3 items)
(1, 501, 2, 15.99, 31.98),
(1, 502, 1, 25.50, 25.50),
(1, 503, 3, 9.33, 27.99),

-- Order 2 items (3 items)  
(2, 504, 1, 49.99, 49.99),
(2, 505, 2, 22.75, 45.50),
(2, 506, 4, 11.75, 47.01),

-- Order 3 items (3 items)
(3, 507, 1, 35.00, 35.00),
(3, 508, 3, 12.50, 37.50),
(3, 509, 2, 12.38, 24.75);
