"""Daily Kite login helper.

Run this once per trading day to refresh KITE_ACCESS_TOKEN.

Usage:
    python scripts/login.py

It will print a login URL. Open it, log in, copy the request_token from the
redirect URL, paste it back, and the script prints a new access_token.
Update your .env file (or Render env vars) with that token.
"""
import os
import sys
from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("KITE_API_KEY")
api_secret = os.getenv("KITE_API_SECRET")
if not api_key or not api_secret:
    sys.exit("Set KITE_API_KEY and KITE_API_SECRET in .env first")

kite = KiteConnect(api_key=api_key)
print("\n1. Open this URL in your browser and log in:")
print(f"   {kite.login_url()}\n")
print("2. After login you'll be redirected to a URL containing ?request_token=XXXX")
request_token = input("3. Paste the request_token here: ").strip()

session = kite.generate_session(request_token, api_secret=api_secret)
print("\n✓ Success. New access_token:")
print(f"\n   KITE_ACCESS_TOKEN={session['access_token']}\n")
print("Update your .env (local) or Render env vars (production) with this value.")
