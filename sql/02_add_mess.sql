-- Real-world mess, added on purpose.
-- Run right after generate_data.py fills clean data.

-- 1. Missing contact details (customer skipped them at signup)
UPDATE customers SET phone = NULL WHERE customer_id % 20 = 0;
UPDATE customers SET email = NULL WHERE customer_id % 25 = 0;

-- 2. Messy formatting (extra spaces, wrong case)
UPDATE customers SET full_name = '  ' || full_name || ' ' WHERE customer_id % 40 = 0;
UPDATE customers SET email = UPPER(email) WHERE customer_id % 30 = 0 AND email IS NOT NULL;

-- 3. Same person signed up twice (new ID, email in different case)
INSERT INTO customers (full_name, phone, email, city_id, address, created_at, updated_at)
SELECT full_name, phone, UPPER(email), city_id, address,
       created_at + INTERVAL '20 days', updated_at + INTERVAL '20 days'
FROM customers
WHERE customer_id % 50 = 0 AND customer_id <= 1000;

-- 4. Payment type typed differently by different app versions
UPDATE payments SET payment_type = LOWER(payment_type) WHERE payment_id % 50 = 0;
UPDATE payments SET payment_type = payment_type || ' '  WHERE payment_id % 70 = 0;

-- 5. Area names in different case
UPDATE deliveries SET area = LOWER(area) WHERE delivery_id % 60 = 0;

-- 6. Status changed days later (refund after delivery)
UPDATE orders
SET status = 'refunded', updated_at = updated_at + INTERVAL '2 days'
WHERE order_id % 200 = 0 AND status = 'delivered';

-- 7. App bug: marked delivered, but delivered_at was never saved
UPDATE deliveries SET delivered_at = NULL WHERE delivery_id % 100 = 0;

-- 8. Bad amounts
UPDATE orders SET total_amount = 0 WHERE order_id % 500 = 0;

-- 9. Orders pointing to a restaurant that doesn't exist (orphans)
UPDATE orders SET restaurant_id = 999 WHERE order_id % 1000 = 0;