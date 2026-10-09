import random
from datetime import datetime, timedelta

from faker import Faker
import psycopg

fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)

DB_URL = "postgresql://quickbite:quickbite@localhost:5432/quickbite_app"

# ---------------- Settings ----------------

CITIES = [
    ("Pune", "Maharashtra"),
    ("Mumbai", "Maharashtra"),
    ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"),
    ("Delhi", "Delhi"),
]

CITY_CENTERS = {
    1: (18.5204, 73.8567),
    2: (19.0760, 72.8777),
    3: (12.9716, 77.5946),
    4: (17.3850, 78.4867),
    5: (28.6139, 77.2090),
}

AREAS = {
    1: ["Kothrud", "Baner", "Hinjewadi", "Viman Nagar"],
    2: ["Andheri", "Bandra", "Powai", "Dadar"],
    3: ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout"],
    4: ["Gachibowli", "Madhapur", "Banjara Hills", "Kukatpally"],
    5: ["Saket", "Dwarka", "Rohini", "Connaught Place"],
}

NUM_CUSTOMERS = 1000
NUM_RIDERS = 200
NUM_RESTAURANTS = 200
DISHES_PER_RESTAURANT = 10

START_DATE = datetime(2026, 9, 1)
NUM_DAYS = 30
ORDERS_PER_DAY = 500

CANCEL_RATE = 0.05
PAYMENT_FAIL_RATE = 0.05
FAILURE_REASONS = ["bank_timeout", "insufficient_funds", "card_declined", "upi_pin_wrong"]

HOUR_WEIGHTS = [1, 1, 0, 0, 0, 0, 1, 2, 3, 3, 3, 4,
                8, 9, 6, 3, 3, 4, 6, 9, 10, 8, 4, 2]


# ---------------- Helpers ----------------

def restaurant_city(restaurant_id):
    return (restaurant_id - 1) % len(CITIES) + 1


def random_dish(restaurant_id):
    first_dish = (restaurant_id - 1) * DISHES_PER_RESTAURANT + 1
    return random.randint(first_dish, first_dish + DISHES_PER_RESTAURANT - 1)


def random_order_time(day):
    hour = random.choices(range(24), weights=HOUR_WEIGHTS)[0]
    return day + timedelta(hours=hour,
                           minutes=random.randint(0, 59),
                           seconds=random.randint(0, 59))


# ---------------- Steps ----------------

def reset_tables(cur):
    cur.execute("""
        TRUNCATE deliveries, payments, order_items, orders,
                 riders, customers, cities
        RESTART IDENTITY CASCADE;
    """)


def insert_cities(cur):
    cur.executemany(
        "INSERT INTO cities (city_name, state) VALUES (%s, %s)",
        CITIES,
    )


def insert_customers(cur):
    rows = []
    for _ in range(NUM_CUSTOMERS):
        rows.append((
            fake.name(),
            fake.phone_number(),
            fake.email(),
            random.randint(1, len(CITIES)),
            fake.address().replace("\n", ", "),
        ))
    cur.executemany(
        """INSERT INTO customers (full_name, phone, email, city_id, address)
           VALUES (%s, %s, %s, %s, %s)""",
        rows,
    )


def insert_riders(cur):
    rows = []
    for _ in range(NUM_RIDERS):
        rows.append((
            fake.name(),
            fake.phone_number(),
            random.randint(1, len(CITIES)),
            random.choice(["bike", "scooter", "cycle"]),
            random.random() < 0.9,
        ))
    cur.executemany(
        """INSERT INTO riders (full_name, phone, city_id, vehicle_type, is_active)
           VALUES (%s, %s, %s, %s, %s)""",
        rows,
    )


def generate_activity(cur):
    cur.execute("SELECT customer_id, city_id FROM customers")
    customers = cur.fetchall()

    cur.execute("SELECT rider_id, city_id FROM riders WHERE is_active")
    riders_by_city = {}
    for rider_id, city_id in cur.fetchall():
        riders_by_city.setdefault(city_id, []).append(rider_id)

    restaurants_by_city = {}
    for r in range(1, NUM_RESTAURANTS + 1):
        restaurants_by_city.setdefault(restaurant_city(r), []).append(r)

    orders, items, payments, deliveries = [], [], [], []
    order_id = item_id = payment_id = delivery_id = 0

    for d in range(NUM_DAYS):
        day = START_DATE + timedelta(days=d)

        for _ in range(ORDERS_PER_DAY):
            order_id += 1
            customer_id, city_id = random.choice(customers)
            restaurant_id = random.choice(restaurants_by_city[city_id])
            ordered_at = random_order_time(day)

            # Items
            total = 0
            for _ in range(random.randint(1, 4)):
                item_id += 1
                quantity = random.randint(1, 3)
                unit_price = round(random.uniform(80, 450), 2)
                total += quantity * unit_price
                items.append((item_id, order_id, random_dish(restaurant_id),
                              quantity, unit_price, ordered_at))
            total = round(total, 2)

            # Payment (sometimes a failed try first)
            payment_type = random.choices(["UPI", "card", "cash"], weights=[60, 25, 15])[0]
            paid_at = ordered_at + timedelta(seconds=random.randint(5, 60))

            if payment_type != "cash" and random.random() < PAYMENT_FAIL_RATE:
                payment_id += 1
                payments.append((payment_id, order_id, payment_type, total, "failed",
                                 random.choice(FAILURE_REASONS), paid_at, paid_at, paid_at))
                paid_at += timedelta(seconds=random.randint(20, 120))

            payment_id += 1
            payments.append((payment_id, order_id, payment_type, total, "success",
                             None, paid_at, paid_at, paid_at))

            # Delivery (only if not cancelled)
            if random.random() < CANCEL_RATE:
                status = "cancelled"
                last_update = ordered_at + timedelta(minutes=random.randint(1, 10))
            else:
                delivery_id += 1
                assigned_at = ordered_at + timedelta(minutes=random.randint(2, 10))
                picked_up_at = assigned_at + timedelta(minutes=random.randint(10, 25))
                delivered_at = picked_up_at + timedelta(minutes=random.randint(10, 35))
                lat, lon = CITY_CENTERS[city_id]

                deliveries.append((
                    delivery_id, order_id,
                    random.choice(riders_by_city[city_id]),
                    "delivered",
                    random.choice(AREAS[city_id]),
                    round(lat + random.uniform(-0.05, 0.05), 6),
                    round(lon + random.uniform(-0.05, 0.05), 6),
                    assigned_at, picked_up_at, delivered_at,
                    assigned_at, delivered_at,
                ))
                status = "delivered"
                last_update = delivered_at

            orders.append((order_id, customer_id, restaurant_id, city_id, status,
                           total, ordered_at, ordered_at, last_update))

    cur.executemany(
        """INSERT INTO orders (order_id, customer_id, restaurant_id, city_id, status,
                               total_amount, ordered_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        orders,
    )
    cur.executemany(
        """INSERT INTO order_items (order_item_id, order_id, dish_id, quantity,
                                    unit_price, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        items,
    )
    cur.executemany(
        """INSERT INTO payments (payment_id, order_id, payment_type, amount, status,
                                 failure_reason, paid_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        payments,
    )
    cur.executemany(
        """INSERT INTO deliveries (delivery_id, order_id, rider_id, status, area,
                                   drop_lat, drop_long, assigned_at, picked_up_at,
                                   delivered_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        deliveries,
    )

    return len(orders), len(items), len(payments), len(deliveries)


def fix_id_counters(cur):
    for table, column in [("orders", "order_id"),
                          ("order_items", "order_item_id"),
                          ("payments", "payment_id"),
                          ("deliveries", "delivery_id")]:
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"(SELECT MAX({column}) FROM {table}))"
        )


def main():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            reset_tables(cur)
            insert_cities(cur)
            insert_customers(cur)
            insert_riders(cur)
            counts = generate_activity(cur)
            fix_id_counters(cur)
        conn.commit()

    print("Done.")
    print(f"orders={counts[0]}, order_items={counts[1]}, "
          f"payments={counts[2]}, deliveries={counts[3]}")


if __name__ == "__main__":
    main()