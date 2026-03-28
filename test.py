# selenium版本（当上述脚本失败时使用）
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime

def fetch_with_selenium(event_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}/executive"
    
    try:
        driver.get(url)
        print("⏳ 等待页面加载和渲染内容...")
        time.sleep(5)  # 等待JavaScript渲染
        
        # 尝试多种方式定位Tectonic Summary
        content = ""
        
        # 方法1: 通过部分ID匹配
        try:
            element = driver.find_element(By.XPATH, "//*[contains(@id, 'tectonic-summary') or contains(., 'Tectonic Summary')]")
            content = element.text
        except:
            pass
            
        # 方法2: 查找包含"Tectonic Summary"文本的元素
        if not content:
            try:
                header = driver.find_element(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tectonic summary')]")
                content_element = header.find_element(By.XPATH, "./following-sibling::*[1]")
                content = content_element.text
            except:
                pass
        
        # 方法3: 获取整个内容区域
        if not content or len(content) < 100:
            try:
                content_area = driver.find_element(By.CLASS_NAME, "executive-section")
                content = content_area.text
                # 从内容中提取Tectonic Summary部分
                if "Tectonic Summary" in content:
                    parts = content.split("Tectonic Summary")
                    if len(parts) > 1:
                        content = "Tectonic Summary" + parts[1].split("Scientific")[0]  # 假设下一部分是"Scientific"
            except:
                pass
        
        if content and len(content) > 50:
            # 保存内容
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tectonic_summary_selenium_{event_id}_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 成功使用Selenium获取Tectonic Summary!")
            print(f"📄 保存到: {os.path.abspath(output_file)}")
            return True
        else:
            print("❌ 无法找到足够的Tectonic Summary内容")
            return False
            
    finally:
        driver.quit()

# 使用方法:
# fetch_with_selenium("us7000s789")
