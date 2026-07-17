import os
from supabase import create_client

url = "https://oaqiawqxxxaqzcalmxsh.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9hcWlhd3F4eHhhcXpjYWxteHNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyODQ2MzEsImV4cCI6MjA5OTg2MDYzMX0.SwCu3-7ITl3b1qHPCvE1DMk6NkY3B4vMSSGa4fGug1U"

client = create_client(url, anon_key)

try:
    res = client.table("facebook_posts").select("*").execute()
    print("Success! Data:", len(res.data), "rows")
    if res.data:
        print(res.data[0])
except Exception as e:
    print("Error:", e)
