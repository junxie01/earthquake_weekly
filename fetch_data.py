import requests
import json
import datetime
import time
import re
from urllib.parse import quote

def fetch_google_news(query):
    encoded_query = quote(query)
    print(f"  Searching Google News for: {query}")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(rss_url, headers=headers, timeout=15)
        items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
        news = []
        for item in items[:3]:
            title_match = re.search(r'<title>(.*?)</title>', item)
            link_match = re.search(r'<link>(.*?)</link>', item)
            if title_match and link_match:
                full_title = title_match.group(1)
                clean_title = re.sub(r' - [^-]+$', '', full_title).strip()
                news.append({"text": clean_title, "url": link_match.group(1)})
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

    # 1. Calculate Date Range
    all_times = [f['properties']['time'] for f in features if f['properties']['time']]
    start_time = datetime.datetime.utcfromtimestamp(min(all_times)/1000).strftime('%Y-%m-%d') if all_times else "N/A"
    end_time = datetime.datetime.utcfromtimestamp(max(all_times)/1000).strftime('%Y-%m-%d') if all_times else "N/A"

    # 2. Magnitude Statistics
    magnitudes = [f['properties']['mag'] for f in features if f['properties']['mag'] is not None]
    stats = {
        "m4_5": len([m for m in magnitudes if 4.0 <= m < 5.0]),
        "m5_6": len([m for m in magnitudes if 5.0 <= m < 6.0]),
        "m6_7": len([m for m in magnitudes if 6.0 <= m < 7.0]),
        "m7_plus": len([m for m in magnitudes if m >= 7.0])
    }

    sorted_eqs = sorted(
        [f for f in features if f['properties']['mag'] is not None],
        key=lambda x: x['properties']['mag'],
        reverse=True
    )

    results = {
        "update_time": datetime.datetime.utcnow().isoformat(),
        "date_range": f"{start_time} to {end_time}",
        "total_count": len(features),
        "stats": stats,
        "top_3": []
    }

    global_seen_images = set()

    for eq in sorted_eqs[:3]:
        props = eq['properties']
        event_id = eq['id']
        lat, lon = eq['geometry']['coordinates'][1], eq['geometry']['coordinates'][0]

        print(f"Processing Event: {event_id} (M{props['mag']})")
        detail_url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"
        detail_data = requests.get(detail_url, timeout=30).json()

        hist_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
        hist_data = {"features": []}
        try:
            h_resp = requests.get(hist_url, timeout=15)
            if h_resp.status_code == 200: hist_data = h_resp.json()
        except: pass

        products = detail_data.get('properties', {}).get('products', {})

        def get_images(p_type):
            items = products.get(p_type, [])
            imgs = []
            for item in items:
                contents = item.get('contents', {})
                keys = ['fm', 'focal', 'beachball', 'mechanism', 'mpp', 'm_p', 'download'] if p_type in ['moment-tensor', 'focal-mechanism'] else ['intensity', 'pager', 'dyfi_geo']
                for k, v in contents.items():
                    kl, url = k.lower(), v['url']
                    if any(x in kl for x in keys) and kl.endswith(('.png', '.jpg', '.jpeg')) and url not in global_seen_images:
                        imgs.append(url); global_seen_images.add(url)
                if not imgs:
                    for k, v in contents.items():
                        url = v['url']
                        if k.lower().endswith(('.png', '.jpg', '.jpeg')) and url not in global_seen_images:
                            imgs.append(url); global_seen_images.add(url); break
            return list(set(imgs))[:2]

        usgs_reports = {
            "shakemap": {"images": get_images('shakemap'), "title": "Shakemap"},
            "dyfi": {"images": get_images('dyfi'), "title": "DYFI"},
            "moment_tensor": {"images": get_images('moment-tensor'), "title": "Moment Tensor"},
            "focal_mechanism": {"images": get_images('focal-mechanism'), "title": "Focal Mechanism"},
            "losspager": {"images": get_images('losspager'), "title": "PAGER"},
            "tectonic_summary": detail_data.get('properties', {}).get('description')
        }

        public_info = []
        for lp in ['general-link', 'impact-link', 'associated-link']:
            for item in products.get(lp, []):
                p = item.get('properties', {})
                if p.get('url'): public_info.append({"text": p.get('text') or p.get('title'), "url": p.get('url')})
                if len(public_info) >= 3: break
            if len(public_info) >= 3: break

        google_news = fetch_google_news(f"earthquake {props['place'].split(',')[-1].strip()}")

        results['top_3'].append({
            "id": event_id, "mag": props['mag'], "place": props['place'], "time": props['time'], "lat": lat, "lon": lon,
            "usgs_reports": usgs_reports, "public_info": public_info, "google_news": google_news,
            "history_count": len(hist_data.get('features', [])), "history_geojson": hist_data,
            "usgs_url": f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}"
        })
        time.sleep(0.5)

    with open('data.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("SUCCESS: data.json updated.")

if __name__ == "__main__":
    fetch_data()
