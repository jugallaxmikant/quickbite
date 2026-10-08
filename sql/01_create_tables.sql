-- QuickBite app database: source tables
-- Safe to run many times (IF NOT EXISTS)

-- Things that exist ------------------------------------------

CREATE TABLE IF NOT EXISTS cities (
    city_id     SERIAL PRIMARY KEY,
    city_name   TEXT NOT NULL,
    state       TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id  SERIAL PRIMARY KEY,
    full_name    TEXT NOT NULL,
    phone        TEXT,
    email        TEXT,
    city_id      INT REFERENCES cities(city_id),
    address      TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS riders (
    rider_id      SERIAL PRIMARY KEY,
    full_name     TEXT NOT NULL,
    phone         TEXT,
    city_id       INT REFERENCES cities(city_id),
    vehicle_type  TEXT,                 -- bike, scooter, cycle
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Things that happen -----------------------------------------

CREATE TABLE IF NOT EXISTS orders (
    order_id       SERIAL PRIMARY KEY,
    customer_id    INT NOT NULL REFERENCES customers(customer_id),
    restaurant_id  INT NOT NULL,        -- from Restaurant API, so no foreign key here
    city_id        INT REFERENCES cities(city_id),
    status         TEXT NOT NULL,       -- placed, accepted, preparing, picked_up, delivered, cancelled
    total_amount   NUMERIC(10, 2) NOT NULL,
    ordered_at     TIMESTAMP NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  SERIAL PRIMARY KEY,
    order_id       INT NOT NULL REFERENCES orders(order_id),
    dish_id        INT NOT NULL,        -- from Restaurant API, so no foreign key here
    quantity       INT NOT NULL,
    unit_price     NUMERIC(10, 2) NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id      SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES orders(order_id),
    payment_type    TEXT NOT NULL,      -- UPI, card, cash
    amount          NUMERIC(10, 2) NOT NULL,
    status          TEXT NOT NULL,      -- success, failed
    failure_reason  TEXT,               -- empty when status = success
    paid_at         TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id    SERIAL PRIMARY KEY,
    order_id       INT NOT NULL REFERENCES orders(order_id),
    rider_id       INT REFERENCES riders(rider_id),
    status         TEXT NOT NULL,       -- assigned, picked_up, delivered, failed
    area           TEXT,
    drop_lat       NUMERIC(9, 6),
    drop_long      NUMERIC(9, 6),
    assigned_at    TIMESTAMP,
    picked_up_at   TIMESTAMP,
    delivered_at   TIMESTAMP,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW()
);