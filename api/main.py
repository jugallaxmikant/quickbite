import math
import random
from datetime import datetime, timedelta

from faker import Faker
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="QuickBite Restaurant Partner API")

# Same rules as scripts/generate_data.py
CITIES = {1: "Pune", 2: "Mumbai", 3: "Bengaluru", 4: "Hyderabad", 5: "Delhi"}
AREAS = {
    1: ["Kothrud", "Baner", "Hinjewadi", "Viman Nagar"],
    2: ["Andheri", "Bandra", "Powai", "Dadar"],
    3: ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout"],
    4: ["Gachibowli", "Madhapur", "Banjara Hills", "Kukatpally"],
    5: ["Saket", "Dwarka", "Rohini", "Connaught Place"],
}
NUM_RESTAURANTS = 200
DISHES_PER_RESTAURANT = 10

MENUS = {
    "North Indian": ["Paneer Butter Masala", "Dal Makhani", "Butter Naan", "Chole Bhature",
                     "Veg Biryani", "Rajma Chawal", "Aloo Paratha", "Kadai Paneer",
                     "Jeera Rice", "Gulab Jamun"],
    "South Indian": ["Masala Dosa", "Idli Sambar", "Medu Vada", "Uttapam", "Rava Dosa",
                     "Lemon Rice", "Curd Rice", "Pongal", "Upma", "Filter Coffee"],
    "Chinese": ["Hakka Noodles", "Veg Manchurian", "Fried Rice", "Chilli Paneer",
                "Spring Rolls", "Schezwan Noodles", "Momos", "Hot and Sour Soup",
                "Chilli Potato", "Manchow Soup"],
    "Italian": ["Margherita Pizza", "Farmhouse Pizza", "Pasta Alfredo", "Pasta Arrabiata",
                "Garlic Bread", "Lasagna", "Bruschetta", "Risotto", "Minestrone", "Tiramisu"],
    "Fast Food": ["Veg Burger", "Chicken Burger", "French Fries", "Chicken Wrap",
                  "Paneer Wrap", "Club Sandwich", "Hot Dog", "Nachos", "Cold Coffee",
                  "Chocolate Shake"],
}


def restaurant_city(restaurant_id):
    return (restaurant_id - 1) % len(CITIES) + 1


def build_data():
    """Create the same restaurants and dishes every time the API starts."""
    rng = random.Random(7)
    fake = Faker("en_IN")
    Faker.seed(7)
    base_time = datetime(2026, 9, 1)

    restaurants, dishes = [], []
    for rid in range(1, NUM_RESTAURANTS + 1):
        city_id = restaurant_city(rid)
        cuisine = rng.choice(list(MENUS))
        restaurants.append({
            "restaurant_id": rid,
            "name": f"{fake.last_name()}'s {cuisine} Kitchen",
            "city_id": city_id,
            "city_name": CITIES[city_id],
            "area": rng.choice(AREAS[city_id]),
            "cuisine": cuisine,
            "rating": round(rng.uniform(3.0, 5.0), 1),
            "is_open": rng.random() < 0.95,
            "updated_at": (base_time + timedelta(minutes=rng.randint(0, 43200))).isoformat() + "Z",
        })

        first_dish = (rid - 1) * DISHES_PER_RESTAURANT + 1
        for i, dish_name in enumerate(MENUS[cuisine]):
            dishes.append({
                "dish_id": first_dish + i,
                "restaurant_id": rid,
                "dish_name": dish_name,
                "price": round(rng.uniform(80, 450), 2),
                "is_veg": "Chicken" not in dish_name,
                "updated_at": (base_time + timedelta(minutes=rng.randint(0, 43200))).isoformat() + "Z",
            })
    return restaurants, dishes


RESTAURANTS, DISHES = build_data()


def paginate(items, page, page_size):
    """Return one page of items, plus info to find the next page."""
    total_pages = math.ceil(len(items) / page_size)
    start = (page - 1) * page_size
    return {
        "data": items[start:start + page_size],
        "page": page,
        "page_size": page_size,
        "total_items": len(items),
        "total_pages": total_pages,
        "next_page": page + 1 if page < total_pages else None,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/restaurants")
def list_restaurants(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100)):
    return paginate(RESTAURANTS, page, page_size)


@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: int):
    for r in RESTAURANTS:
        if r["restaurant_id"] == restaurant_id:
            return r
    raise HTTPException(status_code=404, detail="Restaurant not found")


@app.get("/dishes")
def list_dishes(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100)):
    return paginate(DISHES, page, page_size)