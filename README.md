# Weekly Earthquake Report (USGS Insights)

这是一个基于 USGS 数据实时生成的地震周报系统。它会自动抓取过去一周全球发生的地震，挑选震级最大的三个事件进行深度分析，包括局部历史地震对比、地质构造总结以及来自 USGS 和 Google News 的多源报道。

## 🌟 功能特点

- **全球地震图**：实时展示过去 7 天全球地震分布，震级越大圆圈越大。
- **板块边界展示**：在地图上叠加全球地质板块边界（Tectonic Plates）。
- **重大地震深度分析**：
    - **局部地图**：自动定位震中，展示 10 度范围内的地理细节。
    - **历史对比**：自动调取 1970 年以来该区域所有 M5.0+ 的历史地震（蓝色圆圈）。
    - **视觉化报告**：直接嵌入 USGS 官方生成的 **Shakemap (烈度图)**、**Moment Tensor (震源球)**、**PAGER (损失预估)** 等专业图表。
    - **多源新闻**：集成 USGS 内部报告链接和 **Google News** 实时搜索结果。
- **全自动更新**：利用 GitHub Actions 每周日凌晨（UTC）自动运行抓取脚本并更新网页。

## 🛠️ 技术栈

- **前端**: HTML5, CSS3, JavaScript (Leaflet.js)
- **后端**: Python 3 (Requests, Regex)
- **数据源**: [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/)
- **自动化**: GitHub Actions

## 🚀 本地运行

1. **安装依赖**:
   ```bash
   pip3 install requests
   ```

2. **抓取最新数据**:
   ```bash
   python3 fetch_data.py
   ```

3. **启动预览服务器**:
   ```bash
   python3 -m http.server 8000
   ```
   访问 `http://localhost:8000` 即可查看。

## 🤖 自动化部署 (GitHub Actions)

项目已配置 `.github/workflows/update_earthquakes.yml`。
- **定时运行**: 每周日 00:00 UTC。
- **手动触发**: 在 GitHub 仓库的 `Actions` 页面选择 "Update Earthquake Data" 并运行。

## 🔗 集成到您的网站 (如 Hexo)

您可以使用 `iframe` 将此页面无缝嵌入到您的个人网站中。

---
*Created by [Jun Xie](https://www.seis-jun.xyz/)*
