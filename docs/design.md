# QuickBite Design Doc

## 1. Problem
QuickBite is a food delivery company. Data about orders, payments, deliveries, and restaurants is created every minute. Managers need this data to make business decisions, but it sits in different source systems and is not ready to use.

This pipeline pulls data from the sources, stores a raw copy, cleans it, and builds business tables that answer the questions below every day.

## 2. Business questions
1. Top 10 dishes by number of orders, per city, per day
2. Number of orders, active customers, order value (GMV), and revenue, per city, per day
3. Number of deliveries and average delivery time, per area, per hour
4. Number and value of payments, per payment type (UPI, card, cash), per day
5. Number of failed payments, per failure reason, per payment type, per day

## 3. Data we need

### Things that exist
| Table | Main columns |
|---|---|
| customers | name, phone, email, city, address |
| restaurants | name, city, area, location, cuisine |
| dishes | dish name, price, restaurant |
| riders | name, phone, city, vehicle type |
| cities | city name, state |

### Things that happen
| Table | Main columns |
|---|---|
| orders | customer, restaurant, order time, status, total amount |
| order_items | order, dish, quantity, price |
| payments | order, payment type, amount, status (success or failed), failure reason |
| deliveries | order, rider, pickup time, drop time, location |

## 4. Sources
| Table | Source |
|---|---|
| customers | Postgres |
| riders | Postgres |
| cities | Postgres |
| orders | Postgres |
| order_items | Postgres |
| payments | Postgres |
| deliveries | Postgres |
| restaurants | Restaurant API |
| dishes | Restaurant API |

Rule: data created inside the QuickBite app comes from Postgres. Data managed by restaurants comes from the Restaurant API.

## 5. Data size

### Assumptions
- 5 cities, 2,000 restaurants, 100,000 customers
- 20,000 orders per day (total, not per city)
- 3 items per order on average
- 1 payment per order, 5% fail first and are retried once

### Rows per day
| Table | Math | Rows per day |
|---|---|---|
| orders | 20,000 | 20,000 |
| order_items | 20,000 × 3 | 60,000 |
| payments | 20,000 + (5% of 20,000 retries) | 21,000 |

### Rows per year
| Table | Rows per year |
|---|---|
| orders | about 7.3 million |
| order_items | about 22 million |
| payments | about 7.7 million |

### Do we need Spark?
No. Tens of millions of rows per year fit easily on one machine. DuckDB and dbt handle this well.

Spark is needed when data is too big for one machine, such as hundreds of millions or billions of rows per day. That happens in Project 2, when QuickBite grows 1000 times.

## 6. Data flow
```
Postgres (app database) ──┐
                          ├──► Python pulls data ──► MinIO raw files ──► dbt silver ──► dbt gold ──► Managers
Restaurant API ───────────┘                          (bronze)            (clean)        (business)
```

- **Bronze (MinIO):** raw files, exactly as received from the source. Never changed.
- **Silver (DuckDB):** cleaned data. Fixed types, no duplicates.
- **Gold (DuckDB):** business tables that answer the 5 questions.
- **Airflow:** runs every step daily, in order.
- **Quality checks:** run between each layer. Bad data is stopped before it moves forward.

## 7. Key decisions

### Why keep raw data
If we find a bug in cleaning or business logic, we can rebuild silver and gold from the raw files. We don't need to pull from the sources again.

### Why order_items is a separate table
One order can have many dishes.
- If all dishes go in one column, we can't count or group dishes with SQL.
- If each dish repeats the full order row, order totals get counted many times and money numbers become wrong.

So each table has one clear grain:
- `orders`: one row per order
- `order_items`: one row per dish in an order

The "many" side holds the key of the "one" side. Each item row stores its `order_id` (a foreign key).

`orders`
| order_id | customer | total_amount |
|---|---|---|
| 101 | Rahul | 500 |

`order_items`
| order_item_id | order_id | dish | quantity | price |
|---|---|---|---|---|
| 1 | 101 | pizza | 1 | 400 |
| 2 | 101 | coke | 2 | 50 |

### Why sum only successful payments
A failed payment followed by a retry creates two payment rows for the same order. If we sum all rows, the same money is counted twice. Money numbers must use only successful payments. Failed rows are still kept to answer question 5.