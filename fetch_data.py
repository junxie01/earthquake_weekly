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
    fig, ax = plt.subplots(figsize=(size, size))
    
    # 使用 beach 函数绘制震源球
    # xy=(0, 0) 表示球心的位置
    # width=200 是球的直径
    focmec = [strike, dip, rake]
    beach_plot = beach(focmec, xy=(0, 0), width=200, linewidth=1, facecolor='#3498db')
    
    # 将震源球添加到当前的坐标轴
    ax.add_collection(beach_plot)
    
    # 设置坐标轴范围，否则球可能在视野之外
    ax.set_xlim(-120, 120)
    ax.set_ylim(-120, 120)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 保存图片
    plt.savefig(filename, dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()


def fetch_google_news(query):
    encoded_query = quote(query)
    print(f"  Searching Google News for: {query}")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
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

    # 按震级排序并过滤出前三大地震，确保位置差异
    sorted_eqs = sorted([f for f in features if f['properties']['mag'] is not None], key=lambda x: x['properties']['mag'], reverse=True)
    top_3_eqs = []
    
    for eq in sorted_eqs:
        if len(top_3_eqs) == 0:
            # 添加第一个地震
            top_3_eqs.append(eq)
        else:
            # 检查与前面所有地震的距离
            far_enough = True
            for existing_eq in top_3_eqs:
                # 计算经纬度差
                existing_lat = existing_eq['geometry']['coordinates'][1]
                existing_lon = existing_eq['geometry']['coordinates'][0]
                current_lat = eq['geometry']['coordinates'][1]
                current_lon = eq['geometry']['coordinates'][0]
                
                lat_diff = abs(current_lat - existing_lat)
                lon_diff = abs(current_lon - existing_lon)
                # 检查是否至少有一个方向的差异大于5度
                if lat_diff < 5 and lon_diff < 5:
                    far_enough = False
                    break
            if far_enough:
                top_3_eqs.append(eq)
                if len(top_3_eqs) == 3:
                    break
    
    # 如果找不到足够的地震（可能所有地震都在同一区域），则使用前三个最大的
    if len(top_3_eqs) < 3:
        # 添加剩余的地震，不考虑位置
        remaining_eqs = [eq for eq in sorted_eqs if eq not in top_3_eqs]
        top_3_eqs.extend(remaining_eqs[:3 - len(top_3_eqs)])

    results = {
        "update_time": datetime.datetime.utcnow().isoformat(),
        "date_range": f"{start_time} to {end_time}",
        "total_count": len(features),
        "stats": stats,
        "top_3": []
    }

    global_seen_images = set()

    for i, eq in enumerate(top_3_eqs):
        props = eq['properties']
        event_id = eq['id']
        lat, lon = eq['geometry']['coordinates'][1], eq['geometry']['coordinates'][0]

        print(f"Processing Event: {event_id} (M{props['mag']})" )
        detail_url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"
        detail_data = requests.get(detail_url, timeout=30).json()

        # 获取历史地震数据，不限制返回数量，增加超时时间
        hist_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
        hist_data = {"features": []}
        try:
            h_resp = requests.get(hist_url, timeout=60)  # 增加超时时间到60秒
            if h_resp.status_code == 200:
                hist_data = h_resp.json()
                print(f"  Found {len(hist_data.get('features', []))} historical earthquakes")
                # 确保每个历史地震事件都有深度信息
                for feature in hist_data.get('features', []):
                    if 'geometry' in feature and feature['geometry']['type'] == 'Point':
                        coordinates = feature['geometry']['coordinates']
                        # 确保坐标数组至少有3个元素（经度、纬度、深度）
                        if len(coordinates) < 3:
                            # 如果没有深度信息，添加默认值（0）
                            coordinates.append(0)
                        # 确保 properties 中有 depth 字段
                        if 'properties' not in feature:
                            feature['properties'] = {}
                        if 'depth' not in feature['properties']:
                            # 从 geometry.coordinates 中获取深度
                            feature['properties']['depth'] = coordinates[2]
        except Exception as e:
            print(f"  Error fetching historical data: {e}")
            # 即使出错，也确保 hist_data 是有效的
            hist_data = {"features": []}

        # Extract depth from geometry coordinates (usually the third element)
        depth = eq['geometry']['coordinates'][2] if len(eq['geometry']['coordinates']) > 2 else None

        products = detail_data.get('properties', {}).get('products', {})

        # Extract Focal Mechanism Parameters (Strike, Dip, Rake)
        focal_params = None
        # Priority: moment-tensor -> focal-mechanism
        for p_type in ['moment-tensor', 'focal-mechanism']:
            if p_type in products:
                # Get the first item (usually primary)
                item = products[p_type][0]
                # Look into properties for focal-mechanism parameters
                p = item.get('properties', {})
                if 'nodal-plane-1-strike' in p:
                    focal_params = {
                        "strike": float(p.get('nodal-plane-1-strike')),
                        "dip": float(p.get('nodal-plane-1-dip')),
                        "rake": float(p.get('nodal-plane-1-rake'))
                    }
                    break

        # Fetch Tectonic Summary from region-info page
        tectonic_summary = None
        try:
            # 尝试从 region-info 页面获取 tectonic summary
            region_info_url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}/region-info"
            print(f"  Fetching tectonic summary from: {region_info_url}")
            response = requests.get(region_info_url, timeout=30)
            print(f"  Region-info page status code: {response.status_code}")
            if response.status_code == 200:
                # 保存页面内容到文件，以便调试
                with open(f"region_info_{event_id}.html", "w") as f:
                    f.write(response.text)
                print(f"  Saved region-info page to region_info_{event_id}.html")
                
                # 尝试多种方式提取 tectonic summary
                # 方式1: 直接从 region-info 页面提取，使用更宽松的正则表达式
                summary_match = re.search(r'Tectonic Summary[\s\S]*?<div[^>]*>([\s\S]*?)</div>', response.text)
                if summary_match:
                    print("  Found tectonic summary in region-info page")
                    tectonic_summary = summary_match.group(1).strip()
                else:
                    # 方式2: 尝试查找包含 tectonic summary 的 div
                    summary_match = re.search(r'<div[^>]*tectonic[^>]*>([\s\S]*?)</div>', response.text, re.IGNORECASE)
                    if summary_match:
                        print("  Found tectonic summary in tectonic div")
                        tectonic_summary = summary_match.group(1).strip()
                    else:
                        # 方式3: 尝试从 executive 页面提取
                        executive_url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}/executive"
                        print(f"  Trying executive page: {executive_url}")
                        executive_response = requests.get(executive_url, timeout=30)
                        print(f"  Executive page status code: {executive_response.status_code}")
                        if executive_response.status_code == 200:
                            # 保存 executive 页面内容到文件，以便调试
                            with open(f"executive_{event_id}.html", "w") as f:
                                f.write(executive_response.text)
                            print(f"  Saved executive page to executive_{event_id}.html")
                            
                            # 尝试从 executive 页面提取
                            summary_match = re.search(r'Tectonic Summary[\s\S]*?<div[^>]*>([\s\S]*?)</div>', executive_response.text)
                            if summary_match:
                                print("  Found tectonic summary in executive page")
                                tectonic_summary = summary_match.group(1).strip()
                
                if tectonic_summary:
                    # Clean up HTML tags
                    tectonic_summary = re.sub(r'<[^>]+>', '', tectonic_summary)
                    # Replace multiple newlines with single newline
                    tectonic_summary = re.sub(r'\n+', '\n', tectonic_summary)
                    # Trim whitespace
                    tectonic_summary = tectonic_summary.strip()
                    print(f"  Successfully fetched tectonic summary: {tectonic_summary[:100]}...")
                else:
                    print("  No tectonic summary found")
            else:
                print(f"  Failed to fetch region-info page: {response.status_code}")
        except Exception as e:
            print(f"  Warning: Failed to fetch tectonic summary: {e}")

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
            "losspager": {"images": get_images('losspager'), "title": "PAGER"},
            "tectonic_summary": tectonic_summary
        }

        public_info = []
        for lp in ['general-link', 'impact-link', 'associated-link']:
            for item in products.get(lp, []):
                p = item.get('properties', {})
                if p.get('url'): public_info.append({"text": p.get('text') or p.get('title'), "url": p.get('url')})
                if len(public_info) >= 3: break
            if len(public_info) >= 3: break

        google_news = fetch_google_news(f"earthquake {props['place'].split(',')[-1].strip()}")

        # 生成震源球图片
        beachball_path = None
        if focal_params:
            beachball_filename = f"images/beachball_{i}.png"
            draw_beachball(
                focal_params['strike'],
                focal_params['dip'],
                focal_params['rake'],
                beachball_filename
            )
            beachball_path = beachball_filename

        results['top_3'].append({
            "id": event_id, "mag": props['mag'], "place": props['place'], "time": props['time'], "lat": lat, "lon": lon, "depth": depth,
            "focal_params": focal_params, # STRIKE, DIP, RAKE for canvas plotting
            "beachball_image": beachball_path, # 保存本地震源球图片路径
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
