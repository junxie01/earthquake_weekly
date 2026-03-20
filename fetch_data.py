import requests
import json
import datetime
import time
import re
from urllib.parse import quote

def fetch_google_news(query):
    """
    Improved Google News fetcher using RSS with better parsing.
    """
    encoded_query = quote(query)
    print(f"  Searching Google News for: {query}")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(rss_url, headers=headers, timeout=15)

        # More robust regex to capture <item> content
        items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)

        news = []
        for item in items[:3]:
            title_match = re.search(r'<title>(.*?)</title>', item)
            link_match = re.search(r'<link>(.*?)</link>', item)
            if title_match and link_match:
                # Clean up title (remove source suffix like " - CNN")
                full_title = title_match.group(1)
                clean_title = re.sub(r' - [^-]+$', '', full_title).strip()
                news.append({
                    "text": clean_title,
                    "url": link_match.group(1)
                })
        return news
    except Exception as e:
        print(f"    Warning: Google News search failed: {e}")
        return []

def fetch_data():
    print("Fetching weekly earthquake data...")
    weekly_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
    try:
        resp = requests.get(weekly_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error fetching weekly data: {e}")
        return

    features = data.get('features', [])
    sorted_eqs = sorted(
        [f for f in features if f['properties']['mag'] is not None],
        key=lambda x: x['properties']['mag'],
        reverse=True
    )

    top_3 = sorted_eqs[:3]
    results = {
        "update_time": datetime.datetime.utcnow().isoformat(),
        "total_count": len(features),
        "m5_plus": len([f for f in features if f['properties']['mag'] and f['properties']['mag'] >= 5]),
        "m6_plus": len([f for f in features if f['properties']['mag'] and f['properties']['mag'] >= 6]),
        "top_3": []
    }

    global_seen_images = set()

    for eq in top_3:
        props = eq['properties']
        event_id = eq['id']
        lat, lon = eq['geometry']['coordinates'][1], eq['geometry']['coordinates'][0]

        print(f"Processing Event: {event_id} (M{props['mag']})")

        detail_data = {}
        try:
            detail_url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"
            d_resp = requests.get(detail_url, timeout=30)
            d_resp.raise_for_status()
            detail_data = d_resp.json()
        except Exception as e:
            print(f"  Warning: Could not fetch details for {event_id}")

        hist_data = {"features": []}
        try:
            hist_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
            h_resp = requests.get(hist_url, timeout=30)
            if h_resp.status_code == 200:
                hist_data = h_resp.json()
        except Exception as e:
            print(f"  Warning: Could not fetch history for {event_id}")

        products = detail_data.get('properties', {}).get('products', {})

        def get_unique_images(p_type):
            items = products.get(p_type, [])
            imgs = []
            for item in items:
                contents = item.get('contents', {})
                keys = ['fm', 'focal', 'beachball', 'mechanism', 'mpp', 'm_p', 'download'] if p_type in ['moment-tensor', 'focal-mechanism'] else ['intensity', 'pager', 'dyfi_geo']

                for k, v in contents.items():
                    kl = k.lower()
                    url = v['url']
                    if any(x in kl for x in keys) and kl.endswith(('.png', '.jpg', '.jpeg')):
                        if url not in global_seen_images:
                            imgs.append(url)
                            global_seen_images.add(url)

                if not imgs:
                    for k, v in contents.items():
                        url = v['url']
                        if k.lower().endswith(('.png', '.jpg', '.jpeg')):
                            if url not in global_seen_images:
                                imgs.append(url)
                                global_seen_images.add(url)
                                break
            return list(set(imgs))[:2]

        usgs_reports = {
            "shakemap": {"images": get_unique_images('shakemap'), "title": "Shakemap"},
            "dyfi": {"images": get_unique_images('dyfi'), "title": "DYFI"},
            "moment_tensor": {"images": get_unique_images('moment-tensor'), "title": "Moment Tensor"},
            "focal_mechanism": {"images": get_unique_images('focal-mechanism'), "title": "Focal Mechanism"},
            "losspager": {"images": get_unique_images('losspager'), "title": "PAGER"},
            "tectonic_summary": detail_data.get('properties', {}).get('description')
        }

        public_info = []
        for lp in ['general-link', 'impact-link', 'associated-link']:
            for item in products.get(lp, []):
                p = item.get('properties', {})
                if p.get('url'):
                    public_info.append({"text": p.get('text') or p.get('title') or "USGS Report", "url": p.get('url')})
                if len(public_info) >= 3: break
            if len(public_info) >= 3: break

        # Improved news query: use a broader search if place is too specific
        search_place = props['place'].split(',')[-1].strip() # Use country/state for better results
        query = f"earthquake {search_place} M{props['mag']}"
        google_news = fetch_google_news(query)

        results['top_3'].append({
            "id": event_id,
            "mag": props['mag'],
            "place": props['place'],
            "time": props['time'],
            "lat": lat, "lon": lon,
            "usgs_reports": usgs_reports,
            "public_info": public_info,
            "google_news": google_news,
            "history_count": len(hist_data.get('features', [])),
            "history_geojson": hist_data,
            "usgs_url": f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}"
        })
        print(f"  Processed {event_id}: Found {len(public_info)} USGS links and {len(google_news)} Google News.")
        time.sleep(1)

    with open('data.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSUCCESS: data.json has been updated.")

if __name__ == "__main__":
    fetch_data()
