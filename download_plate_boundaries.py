import requests
import json

def download_plate_boundaries():
    print("Downloading plate boundaries data...")
    
    # URL 1: 使用 fraxen/tectonicplates GitHub 仓库的数据
    # 这个仓库提供了 PB2002 板块边界数据
    url = "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json"
    
    try:
        print(f"Downloading from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"Successfully downloaded plate boundaries data")
        print(f"Total features: {len(data.get('features', []))}")
        
        # 保存到本地文件
        with open('pb2002_boundaries.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print("pb2002_boundaries.json updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error downloading plate boundaries: {e}")
        return False

if __name__ == "__main__":
    download_plate_boundaries()
