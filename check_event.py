
import requests
import json

event_id = "us6000shnl"
detail_url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"

print(f"Fetching data for event {event_id}...")
detail_data = requests.get(detail_url, timeout=30).json()

products = detail_data.get('properties', {}).get('products', {})

# Check moment-tensor product
if 'moment-tensor' in products:
    print("\nFound moment-tensor product!")
    item = products['moment-tensor'][0]
    p = item.get('properties', {})
    
    print("\nAvailable properties:")
    for key in sorted(p.keys()):
        if 'nodal' in key:
            print(f"  {key}: {p[key]}")

print("\nDone!")
