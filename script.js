const DATA_JSON_URL = 'data.json';
const PLATE_BOUNDARIES_URL = 'https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json';
const USGS_WEEKLY_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson';

document.addEventListener('DOMContentLoaded', () => {
    loadApp();
});

async function loadApp() {
    try {
        const [storedDataResp, platesResp, currentEqsResp] = await Promise.all([
            fetch(DATA_JSON_URL),
            fetch(PLATE_BOUNDARIES_URL),
            fetch(USGS_WEEKLY_URL)
        ]);

        const data = await storedDataResp.json();
        const plates = await platesResp.json();
        const currentEqs = await currentEqsResp.json();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';

        console.log('Data loaded:', data);
        console.log('Top 3 earthquakes:', data.top_3);

        initMainMap(currentEqs, plates);
        renderStats(data);
        renderTopThree(data, plates);
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('loading').innerHTML = `<p>Seismic analysis in progress or data unavailable.</p>`;
    }
}

function initMainMap(data, plates) {
    const map = L.map('main-map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
    L.geoJSON(plates, { style: { color: 'orange', weight: 1.5, dashArray: '5, 5' } }).addTo(map);
    
    const features = data.features || [];
    const times = features.map(f => f.properties.time);
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    
    L.geoJSON(data, {
        pointToLayer: (f, latlng) => L.circleMarker(latlng, {
            radius: Math.max(f.properties.mag * 2.2, 2),
            fillColor: getColorByTime(f.properties.time, minTime, maxTime),
            color: "#000", weight: 0.5, fillOpacity: 0.7
        }),
        onEachFeature: (f, layer) => {
            layer.bindPopup(`<strong>M${f.properties.mag}</strong> - ${f.properties.place}<br>${new Date(f.properties.time).toLocaleString()}`);
        }
    }).addTo(map);
    
    addLegend(map, minTime, maxTime);
}

function getColorByTime(time, minTime, maxTime) {
    const t = (time - minTime) / (maxTime - minTime);
    return getHeatColor(t);
}

function getHeatColor(t) {
    if (t < 0.2) return '#2ca02c';
    if (t < 0.4) return '#98df8a';
    if (t < 0.6) return '#ffbb78';
    if (t < 0.8) return '#ff7f0e';
    return '#d62728';
}

function addLegend(map, minTime, maxTime) {
    const legend = L.control({ position: 'bottomright' });
    let legendDiv = null;
    let toggleButton = null;
    
    legend.onAdd = function(map) {
        const container = L.DomUtil.create('div', 'legend-container');
        
        toggleButton = L.DomUtil.create('div', 'legend-toggle', container);
        toggleButton.innerHTML = 'i';
        toggleButton.title = 'Show legend';
        toggleButton.style.cssText = `
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: white;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            position: absolute;
            bottom: 10px;
            right: 10px;
            z-index: 1000;
        `;
        
        legendDiv = L.DomUtil.create('div', 'info legend', container);
        legendDiv.style.cssText = `
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            position: absolute;
            bottom: 50px;
            right: 10px;
            max-width: 250px;
        `;
        
        const closeBtn = L.DomUtil.create('div', 'legend-close', legendDiv);
        closeBtn.innerHTML = '×';
        closeBtn.title = 'Close legend';
        closeBtn.style.cssText = `
            position: absolute;
            top: 5px;
            right: 8px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            color: #666;
            line-height: 1;
        `;
        
        let grades = [
            { label: 'Magnitude', values: [3, 4, 5, 6, 7, 8] },
            { label: 'Time (Recent → Old)', values: [1, 0.8, 0.6, 0.4, 0.2, 0] }
        ];
        
        legendDiv.innerHTML = '<strong style="margin-right: 25px; display: block;">Legend</strong>' + legendDiv.innerHTML;
        
        grades.forEach((grade, i) => {
            legendDiv.innerHTML += `<br><strong>${grade.label}:</strong><br>`;
            grade.values.forEach((v, j) => {
                const color = i === 0 ? getMagnitudeColor(v) : getHeatColor(v);
                const size = i === 0 ? Math.max(v * 2.2, 2) * 2 : 8;
                const label = i === 0 ? `M${v}` : (v === 1 ? 'Now' : (v === 0 ? '7 days ago' : ''));
                legendDiv.innerHTML += `<div style="display: flex; align-items: center; margin: 2px 0;">
                    <div style="width: ${size}px; height: ${size}px; border-radius: 50%; background: ${color}; border: 1px solid #000; margin-right: 5px;"></div>
                    <span>${label}</span>
                </div>`;
            });
        });
        
        legendDiv.appendChild(closeBtn);
        
        L.DomEvent.on(closeBtn, 'click', function(e) {
            L.DomEvent.stopPropagation(e);
            legendDiv.style.display = 'none';
            toggleButton.style.display = 'flex';
        });
        
        L.DomEvent.on(toggleButton, 'click', function(e) {
            L.DomEvent.stopPropagation(e);
            legendDiv.style.display = 'block';
            toggleButton.style.display = 'none';
        });
        
        toggleButton.style.display = 'none';
        
        return container;
    };
    
    legend.addTo(map);
}

function getMagnitudeColor(mag) {
    return mag > 7 ? '#800026' : mag > 6 ? '#BD0026' : mag > 5 ? '#E31A1C' : mag > 4 ? '#FC4E2A' : mag > 3 ? '#FD8D3C' : '#FEB24C';
}

function renderStats(data) {
    if (data.date_range) document.getElementById('date-range-display').innerText = `Report Period: ${data.date_range}`;
    if (data.stats) {
        document.getElementById('stat-total').innerText = data.total_count || 0;
        document.getElementById('stat-m45').innerText = data.stats.m4_5 || 0;
        document.getElementById('stat-m56').innerText = data.stats.m5_6 || 0;
        document.getElementById('stat-m67').innerText = data.stats.m6_7 || 0;
        document.getElementById('stat-m7plus').innerText = data.stats.m7_plus || 0;
    }
}

/**
 * 绘制震源球 (Simplified Focal Mechanism Plotter)
 */
function drawBeachball(canvasId, strike, dip, rake) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const r = w / 2 - 5;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    // 背景大圆 (白色)
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((strike * Math.PI) / 180);

    // 根据rake角判断并绘制震源球
    if (Math.abs(rake) < 30 || Math.abs(rake - 180) < 30 || Math.abs(rake + 180) < 30) {
        // 走滑断层类型
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, r, -Math.PI / 2, Math.PI / 2, false);
        ctx.closePath();
        ctx.fillStyle = "#3498db";
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(0, -r);
        ctx.lineTo(0, r);
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 2;
        ctx.stroke();
    } else if (rake > 0) {
        // 逆断层类型
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI, false);
        ctx.fillStyle = "#3498db";
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(-r, 0);
        ctx.lineTo(r, 0);
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 2;
        ctx.stroke();
    } else {
        // 正断层类型
        ctx.beginPath();
        ctx.arc(0, 0, r, Math.PI, 2 * Math.PI, false);
        ctx.fillStyle = "#3498db";
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(-r, 0);
        ctx.lineTo(r, 0);
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    ctx.restore();
    
    // 重新绘制外圆确保它在最上层
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;
    ctx.stroke();
}

function renderTopThree(data, plates) {
    const container = document.getElementById('top-earthquakes');
    container.innerHTML = '';
    if (!data.top_3) return;

    data.top_3.forEach((eq, i) => {
        const card = document.createElement('div');
        card.className = 'eq-card';
        const reports = eq.usgs_reports;

        let mediaHTML = '';

        // 1. 首先使用本地生成的震源球图片
        if (eq.beachball_image) {
            mediaHTML += `
                <div class="media-item">
                    <img src="${eq.beachball_image}" alt="Focal Mechanism" onclick="window.open('${eq.beachball_image}', '_blank')">
                    <div class="media-caption">Focal Mechanism<br>
                    <small>S:${eq.focal_params.strike}° D:${eq.focal_params.dip}° R:${eq.focal_params.rake}°</small></div>
                </div>
            `;
        } else if (eq.focal_params) {
            // 如果没有本地图片，作为后备使用 Canvas 绘制
            mediaHTML += `
                <div class="media-item">
                    <img src="${eq.beachball_image}" alt="Focal Mechanism" onclick="window.open('${eq.beachball_image}', '_blank')">
                    <div class="media-caption">Focal Mechanism<br>
                    <small>S:${eq.focal_params.strike}° D:${eq.focal_params.dip}° R:${eq.focal_params.rake}°</small></div>
                </div>
            `;
        }

        const reportTypes = ['shakemap', 'losspager', 'dyfi', 'focal_mechanism', 'moment_tensor'];
        reportTypes.forEach(type => {
            const report = reports[type];
            if (report && report.images && report.images.length > 0) {
                const imgsToDisplay = (type === 'shakemap') ? [report.images[0]] : report.images;
                imgsToDisplay.forEach(imgUrl => {
                    mediaHTML += `
                        <div class="media-item">
                            <img src="${imgUrl}" alt="${report.title}" onclick="window.open('${imgUrl}', '_blank')">
                            <div class="media-caption">${report.title} Visualization</div>
                        </div>
                    `;
                });
            }
        });

        let googleNewsHTML = (eq.google_news && eq.google_news.length > 0)
            ? eq.google_news.map(n => `<li><a href="${n.url}" target="_blank">${n.text}</a></li>`).join('')
            : '<li>No matching Google News found.</li>';

        card.innerHTML = `
            <div class="eq-header">
                <h3>#${i + 1}: Magnitude ${eq.mag} - ${eq.place}</h3>
                <p><strong>Time:</strong> ${new Date(eq.time).toUTCString()}</p>
                <p><strong>Location:</strong> ${eq.lat.toFixed(4)}°N, ${eq.lon.toFixed(4)}°E</p>
                <p><strong>Depth:</strong> ${eq.depth ? eq.depth.toFixed(2) : 'N/A'} km</p>
            </div>
            <div id="local-map-${i}" class="local-map"></div>
            <p><strong>Regional Context:</strong> ${eq.history_count} historical earthquakes (M5.0+) within 10° since 1970.</p>

            <div style="margin: 10px 0;">
                <p style="margin:0 0 10px 0;"><strong>Regional Context:</strong> ${eq.history_count} historical earthquakes (M5.0+) within 10° since 1970.</p>
                <a href="${eq.usgs_url}" target="_blank" class="btn" style="color: #fff !important; font-weight: bold; background-color: #3498db; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 0.9em;">Full USGS Event Page</a>
            </div>

            <div class="media-grid">${mediaHTML || '<p style="padding: 20px; color: #666;">Waiting for USGS to process visual reports...</p>'}</div>

            <div class="report-section" style="grid-template-columns: 1fr;">
                <div class="report-box" style="border-left-color: #f1c40f;">
                    <h4>Latest News & Official Data</h4>
                    <ul style="margin-bottom: 5px;">${googleNewsHTML}</ul>
                </div>
            </div>

            ${reports.tectonic_summary ? `
                <div style="margin-top: 15px;">
                    <strong>Tectonic Summary:</strong>
                    <div class="tectonic-summary">${reports.tectonic_summary}</div>
                </div>
            ` : ''}
        `;
        container.appendChild(card);

        // 绘图执行 - 只有在没有本地震源球图片时才绘制
        if (!eq.beachball_image && eq.focal_params) {
            drawBeachball(`beachball-${i}`, eq.focal_params.strike, eq.focal_params.dip, eq.focal_params.rake);
        }

        const localMap = L.map(`local-map-${i}`).setView([eq.lat, eq.lon], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(localMap);
        L.geoJSON(plates, { style: { color: 'orange', weight: 2 } }).addTo(localMap);
        
        const historyFeatures = eq.history_geojson?.features || [];
        const historyTimes = historyFeatures.map(f => f.properties.time);
        const minHistoryTime = Math.min(...historyTimes);
        const maxHistoryTime = Math.max(...historyTimes);
        
        if (eq.history_geojson) {
            L.geoJSON(eq.history_geojson, {
                pointToLayer: (f, latlng) => {
                    if (f.id === eq.id) return null;
                    const radius = Math.max(f.properties.mag * 1.5, 2);
                    const fillColor = getColorByTime(f.properties.time, minHistoryTime, maxHistoryTime);
                    return L.circleMarker(latlng, {
                        radius: radius,
                        color: '#666',
                        weight: 0.5,
                        fillColor: fillColor,
                        fillOpacity: 0.5
                    });
                },
                onEachFeature: (f, layer) => layer.bindPopup(`M${f.properties.mag} - ${new Date(f.properties.time).getFullYear()}`)
            }).addTo(localMap);
        }
        
        const mainCircle = L.circleMarker([eq.lat, eq.lon], {
            radius: 12,
            color: '#d32f2f',
            fillColor: '#d32f2f',
            fillOpacity: 0.9,
            weight: 2
        }).addTo(localMap);
        
        mainCircle.bringToFront();
        
        let isVisible = true;
        setInterval(() => {
            isVisible = !isVisible;
            mainCircle.setStyle({
                fillOpacity: isVisible ? 0.9 : 0.2,
                opacity: isVisible ? 1 : 0.4
            });
        }, 800);
        
        addLocalLegend(localMap, minHistoryTime, maxHistoryTime);
    });
}

function addLocalLegend(map, minTime, maxTime) {
    const legend = L.control({ position: 'bottomright' });
    let legendDiv = null;
    let toggleButton = null;
    
    legend.onAdd = function(map) {
        const container = L.DomUtil.create('div', 'legend-container');
        
        toggleButton = L.DomUtil.create('div', 'legend-toggle', container);
        toggleButton.innerHTML = 'i';
        toggleButton.title = 'Show legend';
        toggleButton.style.cssText = `
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: white;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0,0,0,0.2);
            position: absolute;
            bottom: 8px;
            right: 8px;
            z-index: 1000;
        `;
        
        legendDiv = L.DomUtil.create('div', 'info legend', container);
        legendDiv.style.cssText = `
            background: white;
            padding: 8px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            font-size: 0.85em;
            position: absolute;
            bottom: 40px;
            right: 8px;
            max-width: 200px;
        `;
        
        const closeBtn = L.DomUtil.create('div', 'legend-close', legendDiv);
        closeBtn.innerHTML = '×';
        closeBtn.title = 'Close legend';
        closeBtn.style.cssText = `
            position: absolute;
            top: 3px;
            right: 6px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            color: #666;
            line-height: 1;
        `;
        
        let grades = [
            { label: 'Magnitude', values: [3, 4, 5, 6, 7, 8] },
            { label: 'Time (Recent → Old)', values: [1, 0.8, 0.6, 0.4, 0.2, 0] }
        ];
        
        legendDiv.innerHTML = '<strong style="margin-right: 20px; display: block;">Legend</strong>' + legendDiv.innerHTML;
        
        grades.forEach((grade, i) => {
            legendDiv.innerHTML += `<br><strong>${grade.label}:</strong><br>`;
            grade.values.forEach((v, j) => {
                const color = i === 0 ? getMagnitudeColor(v) : getHeatColor(v);
                const size = i === 0 ? Math.max(v * 1.5, 2) * 1.2 : 6;
                const label = i === 0 ? `M${v}` : (v === 1 ? 'Recent' : (v === 0 ? '1970' : ''));
                legendDiv.innerHTML += `<div style="display: flex; align-items: center; margin: 1px 0;">
                    <div style="width: ${size}px; height: ${size}px; border-radius: 50%; background: ${color}; border: 1px solid #666; margin-right: 4px;"></div>
                    <span>${label}</span>
                </div>`;
            });
        });
        
        legendDiv.appendChild(closeBtn);
        
        L.DomEvent.on(closeBtn, 'click', function(e) {
            L.DomEvent.stopPropagation(e);
            legendDiv.style.display = 'none';
            toggleButton.style.display = 'flex';
        });
        
        L.DomEvent.on(toggleButton, 'click', function(e) {
            L.DomEvent.stopPropagation(e);
            legendDiv.style.display = 'block';
            toggleButton.style.display = 'none';
        });
        
        toggleButton.style.display = 'none';
        
        return container;
    };
    
    legend.addTo(map);
}
