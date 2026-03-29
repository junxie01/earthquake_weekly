import requests
import json

def test_usgs_api():
    # 测试日本附近的坐标（与截图中的地震位置类似）
    lat = 39.4462
    lon = 143.3717
    
    # 原来的 API URL
    url1 = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
    
    print("测试 1 - 原 API URL:")
    print(f"URL: {url1}")
    try:
        response = requests.get(url1, timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"找到 {len(data.get('features', []))} 个地震")
        else:
            print(f"响应内容: {response.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 添加 endtime 参数
    endtime = "2026-03-29"
    url2 = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1970-01-01&endtime={endtime}&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=5.0"
    
    print("测试 2 - 添加 endtime 参数:")
    print(f"URL: {url2}")
    try:
        response = requests.get(url2, timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"找到 {len(data.get('features', []))} 个地震")
            if data.get('features'):
                print(f"前3个地震:")
                for i, f in enumerate(data['features'][:3]):
                    print(f"  {i+1}. M{f['properties']['mag']} - {f['properties']['place']}")
        else:
            print(f"响应内容: {response.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_usgs_api()
