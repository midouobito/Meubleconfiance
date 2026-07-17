import os
import sys
from supabase import create_client

sys.path.append(os.path.join(os.getcwd(), 'fb_scraper'))
import config

client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

# Test products table
print("Testing products table...")
res = client.table("products").select("id").limit(1).execute()
print("Products:", res.data)

# Test storage
print("Testing storage buckets...")
res = client.storage.list_buckets()
for b in res:
    print(f"Bucket: {b.name}, public: {b.public}")
