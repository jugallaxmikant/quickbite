import json
import time
from datetime import date

import boto3
import requests
from botocore.config import Config

API_URL = "http://localhost:8000"
BUCKET = "bronze"
MAX_RETRIES = 5

# Connect to our S3 storage (SeaweedFS)
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:8333",
    aws_access_key_id="any",
    aws_secret_access_key="any",
    region_name="us-east-1",
    config=Config(s3={"addressing_style": "path"}),
)


def get_with_retry(url, params):
    """Ask the API. On 429 or 5xx, wait and try again, up to MAX_RETRIES times."""
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
        elif response.status_code >= 500:
            wait = 2 ** (attempt - 1)          # 1, 2, 4, 8, 16 seconds
        else:
            response.raise_for_status()        # other 4xx: don't retry, stop

        print(f"  got {response.status_code} (attempt {attempt}), waiting {wait}s")
        time.sleep(wait)

    raise RuntimeError(f"Gave up after {MAX_RETRIES} tries: {url}")


def clear_folder(endpoint, run_date):
    """Delete all files from this source for this day, before writing new ones."""
    prefix = f"api/{endpoint}/run_date={run_date}/"
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    for obj in response.get("Contents", []):
        s3.delete_object(Bucket=BUCKET, Key=obj["Key"])


def save_page(endpoint, run_date, page, body):
    """Save one page of API data as a JSON file in the bronze bucket."""
    key = f"api/{endpoint}/run_date={run_date}/page_{page:03d}.json"
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(body))
    print(f"saved {key}")


def pull(endpoint, page_size):
    """Ask the API for every page, one by one, and save each one."""
    run_date = date.today().isoformat()
    clear_folder(endpoint, run_date)
    page = 1

    while page is not None:
        response = get_with_retry(
            f"{API_URL}/{endpoint}",
            {"page": page, "page_size": page_size},
        )
        body = response.json()

        save_page(endpoint, run_date, page, body)
        page = body["next_page"]


if __name__ == "__main__":
    pull("restaurants", 50)
    pull("dishes", 100)