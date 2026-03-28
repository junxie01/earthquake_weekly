import requests
import json
import datetime
import time
import re
import os
import math
from urllib.parse import quote
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy.imaging.beachball import beach

def draw_beachball(strike, dip, rake, filename, size=4):
    """
    使用 ObsPy 库专业绘制震源球
    """
    try:
        fig, ax = plt.subplots(figsize=(size, size))
        
        # 使用 beach 函数绘制震源球
        focmec = [strike, dip, rake]
        beach_plot = beach(focmec, xy=(0, 0), width=200, linewidth=1, facecolor='#3498db')
        
        # 将震源球添加到当前的坐标轴
        ax.add_collection(beach_plot)
        
        # 设置坐标轴范围
        ax.set_xlim(-120, 120)
        ax.set_ylim(-120, 120)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 保存图片
        plt.savefig(filename, dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close()
        return True
    except Exception as e:
        print(f"    Error drawing beachball: {e}")
        return False


def fetch_google_news(query):
    """
    获取 Google News 搜索结果
    """
    encoded_query = quote(query)
    print(f"  Searching Google News for: {query}")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(rss_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            print(f"    Warning: Google News returned status {resp.status_code}")
            return []
        
        items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
        news = []
        
        for item in items[:3]:
            title_match = re.search(r'<title>(.*?)</title>', item)
            link_match = re.search(r'<link>(.*?)</link>', item)
            if title_match and link_match:
                full_title = title_match.group(1)
                # 移除末尾的来源信息
                clean_title = re.sub(r' - [^-]+$', '', full_title).strip()
                news.append({"text": clean_title, "url": link_match.group(1)})
        
        print(f"    Found {len(news)} news items")
        return news
        
    except requests.exceptions.Timeout:
        print(f"    Warning: Google News search timed out")
        return []
    except Exception as e:
        print(f"    Warning: Google News search failed: {e}")
        return []


def fetch_with_retry(url, max_retries=3, timeout=30):
    """
    带重试机制的 HTTP 请求
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"    Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
        except Exception as e:
            print(f"    Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None


def fetch_data():
    print("=" * 60)
    print("Fetching weekly earthquake data...")
    print("=" * 60)
    
    weekly_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
    
    try:
        resp = requests.get(weekly_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error fetching weekly data: {e}")
        return

    features = data.get('features', [])
    print(f"Total earthquakes this week: {len(features)}")
    
    if not features:
        print("No earthquake data available")
        return
    
    all_times = [f['properties']['time'] for f in features if f['properties']['time']]
    start_time = datetime.datetime.utcfromtimestamp(min(all_times)/1000).strftime('%Y-%m-%d') if all_times else "N/A"
    end_time = datetime.datetime.utcfromtimestamp(max(all_times)/1000).strftime('%Y-%m-%d') if all_times else "N/A"

    magnitudes = [f['properties']['mag'] for f in features if f['properties']['mag'] is not None]
    stats = {
        "m4_5": len([m for m in magnitudes if 4.0 <= m < 5.0]),
        "m5_6": len([m for m in magnitudes if 5.0 <= m < 6.0]),
        "m6_7": len([m for m in magnitudes if 6.0 <= m < 7.0]),
        "m7_plus": len([m for m in magnitudes if m >= 7.0])
    }

    # 按震级排序
    sorted_eqs = sorted(
        [f for f in features if f['properties']['mag'] is not None], 
        key=lambda x: x['properties']['mag'], 
        reverse=True
    )
    
    # 选择前3个最大的地震
    top_3_eqs = sorted_eqs[:3]
    print(f"\nSelected top {len(top_3_eqs)} earthquakes:")
    for i, eq in enumerate(top_3_eqs):
        print(f"  #{i+1}: M{eq['properties']['mag']} - {eq['properties']['place']}")

    results = {
        "update_time": datetime.datetime.utcnow().isoformat(),
        "date_range": f"{start_time} to {end_time}",
        "total_count": len(features),
        "stats": stats,
        "top_3": []
    }

    global_seen_images = set()

    for i, eq in enumerate(top_3_eqs):
        print(f"\n{'='*60}")
        print(f"Processing Event {i+1}/{len(top_3_eqs)}")
        print(f"{'='*60}")
        
        try:
            props = eq['properties']
            event_id = eq['id']
            lat, lon = eq['geometry']['coordinates'][1], eq['geometry']['coordinates'][0]
            
            print(f"  Event: {event_id}")
            print(f"  Magnitude: M{props['mag']}")
            print(f"  Location: {props['place']}")
            print(f"  Coordinates: {lat}, {lon}")

            # 获取详细信息
            detail_url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"
            print(f"  Fetching details from: {detail_url}")
            
            detail_resp = fetch_with_retry(detail_url, max_retries=3, timeout=30)
            if not detail_resp:
                print(f"    Failed to fetch details after retries, skipping...")
                continue
                
            detail_data = detail_resp.json()

            # 获取历史地震数据
            hist_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
            print(f"  Fetching historical data...")
            
            hist_data = {"features": []}
            hist_resp = fetch_with_retry(hist_url, max_retries=2, timeout=60)
            
            if hist_resp:
                try:
                    hist_data = hist_resp.json()
                    print(f"    Found {len(hist_data.get('features', []))} historical earthquakes")
                    
                    # 确保每个历史地震事件都有深度信息
                    for feature in hist_data.get('features', []):
                        if 'geometry' in feature and feature['geometry']['type'] == 'Point':
                            coordinates = feature['geometry']['coordinates']
                            if len(coordinates) < 3:
                                coordinates.append(0)
                            if 'properties' not in feature:
                                feature['properties'] = {}
                            if 'depth' not in feature['properties']:
                                feature['properties']['depth'] = coordinates[2]
                except Exception as e:
                    print(f"    Error processing historical data: {e}")
            else:
                print(f"    Failed to fetch historical data")

            # 提取深度
            depth = eq['geometry']['coordinates'][2] if len(eq['geometry']['coordinates']) > 2 else None

            products = detail_data.get('properties', {}).get('products', {})

            # 提取震源机制参数
            focal_params = None
            for p_type in ['moment-tensor', 'focal-mechanism']:
                if p_type in products:
                    item = products[p_type][0]
                    p = item.get('properties', {})
                    if 'nodal-plane-1-strike' in p:
                        focal_params = {
                            "strike": float(p.get('nodal-plane-1-strike')),
                            "dip": float(p.get('nodal-plane-1-dip')),
                            "rake": float(p.get('nodal-plane-1-rake'))
                        }
                        print(f"    Focal mechanism found: strike={focal_params['strike']}, dip={focal_params['dip']}, rake={focal_params['rake']}")
                        break

            # 获取 Tectonic Summary
            tectonic_summary = None
            try:
                region_info_url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}/region-info"
                response = fetch_with_retry(region_info_url, max_retries=2, timeout=20)
                
                if response and response.status_code == 200:
                    # 尝试提取 tectonic summary
                    summary_match = re.search(r'Tectonic Summary[\s\S]*?<div[^>]*>([\s\S]*?)</div>', response.text)
                    if summary_match:
                        tectonic_summary = summary_match.group(1).strip()
                        tectonic_summary = re.sub(r'<[^>]+>', '', tectonic_summary)
                        tectonic_summary = re.sub(r'\n+', '\n', tectonic_summary).strip()
                        print(f"    Tectonic summary found")
            except Exception as e:
                print(f"    Warning: Failed to fetch tectonic summary: {e}")

            # 获取图片
            def get_images(p_type):
                items = products.get(p_type, [])
                imgs = []
                for item in items:
                    contents = item.get('contents', {})
                    keys = ['fm', 'focal', 'beachball', 'mechanism', 'mpp', 'm_p', 'download'] if p_type in ['moment-tensor', 'focal-mechanism'] else ['intensity', 'pager', 'dyfi_geo']
                    for k, v in contents.items():
                        kl, url = k.lower(), v['url']
                        if any(x in kl for x in keys) and kl.endswith(('.png', '.jpg', '.jpeg')) and url not in global_seen_images:
                            imgs.append(url)
                            global_seen_images.add(url)
                    if not imgs:
                        for k, v in contents.items():
                            url = v['url']
                            if k.lower().endswith(('.png', '.jpg', '.jpeg')) and url not in global_seen_images:
                                imgs.append(url)
                                global_seen_images.add(url)
                                break
                return list(set(imgs))[:2]

            usgs_reports = {
                "shakemap": {"images": get_images('shakemap'), "title": "Shakemap"},
                "dyfi": {"images": get_images('dyfi'), "title": "DYFI"},
                "losspager": {"images": get_images('losspager'), "title": "PAGER"},
                "tectonic_summary": tectonic_summary
            }

            # 获取公开信息链接
            public_info = []
            for lp in ['general-link', 'impact-link', 'associated-link']:
                for item in products.get(lp, []):
                    p = item.get('properties', {})
                    if p.get('url'):
                        public_info.append({"text": p.get('text') or p.get('title'), "url": p.get('url')})
                    if len(public_info) >= 3:
                        break
                if len(public_info) >= 3:
                    break

            # 获取 Google News
            location = props['place'].split(',')[-1].strip() if ',' in props['place'] else props['place']
            google_news = fetch_google_news(f"earthquake {location}")

            # 生成震源球图片
            beachball_path = None
            if focal_params:
                beachball_filename = f"images/beachball_{i}.png"
                if draw_beachball(
                    focal_params['strike'],
                    focal_params['dip'],
                    focal_params['rake'],
                    beachball_filename
                ):
                    beachball_path = beachball_filename
                    print(f"    Beachball saved to {beachball_filename}")

            # 添加到结果
            results['top_3'].append({
                "id": event_id,
                "mag": props['mag'],
                "place": props['place'],
                "time": props['time'],
                "lat": lat,
                "lon": lon,
                "depth": depth,
                "focal_params": focal_params,
                "beachball_image": beachball_path,
                "usgs_reports": usgs_reports,
                "public_info": public_info,
                "google_news": google_news,
                "history_count": len(hist_data.get('features', [])),
                "history_geojson": hist_data,
                "usgs_url": f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}"
            })
            
            print(f"  ✓ Event {i+1} processed successfully")
            
            # 在事件之间添加短暂延迟
            if i < len(top_3_eqs) - 1:
                time.sleep(1)
                
        except Exception as e:
            print(f"  ✗ Error processing event {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"Processing complete. Total events in results: {len(results['top_3'])}")
    print(f"{'='*60}")

    # 保存结果
    with open('data.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("SUCCESS: data.json updated.")


if __name__ == "__main__":
    fetch_data()
