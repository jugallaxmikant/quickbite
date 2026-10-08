import random
from faker import Faker
import psycopg

fake = Faker("en_IN")        # Indian names, phones, addresses
random.seed(42)              # same random data every run
Faker.seed(42)

DB_URL = "postgresql://quickbite:quickbite@localhost:5432/quickbite_app"

CITIES = [
    ("Pune", "Maharashtra"),
    ("Mumbai", "Maharashtra"),
    ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"),
    ("Delhi", "Delhi"),
]

NUM_CUSTOMERS = 1000
NUM_RIDERS = 200


def reset_tables(cur):
    """Empty all tables so each run starts fresh."""
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
            random.randint(1, len(CITIES)),   # city_id 1 to 5
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
            random.random() < 0.9,            # 90% active
        ))
    cur.executemany(
        """INSERT INTO riders (full_name, phone, city_id, vehicle_type, is_active)
           VALUES (%s, %s, %s, %s, %s)""",
        rows,
    )


def main():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            reset_tables(cur)
            insert_cities(cur)
            insert_customers(cur)
            insert_riders(cur)
        conn.commit()
    print("Done: cities, customers, riders loaded.")


if __name__ == "__main__":
    main()