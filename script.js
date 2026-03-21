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
    L.geoJSON(data, {
        pointToLayer: (f, latlng) => L.circleMarker(latlng, {
            radius: Math.max(f.properties.mag * 2.2, 2),
            fillColor: getColor(f.properties.mag),
            color: "#000", weight: 0.5, fillOpacity: 0.7
        }),
        onEachFeature: (f, layer) => {
            layer.bindPopup(`<strong>M${f.properties.mag}</strong> - ${f.properties.place}<br>${new Date(f.properties.time).toLocaleString()}`);
        }
    }).addTo(map);
}

function getColor(mag) {
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

function renderTopThree(data, plates) {
    const container = document.getElementById('top-earthquakes');
    container.innerHTML = '';
    if (!data.top_3) return;

    data.top_3.forEach((eq, i) => {
        const card = document.createElement('div');
        card.className = 'eq-card';
        const reports = eq.usgs_reports;

        let mediaHTML = '';
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
            </div>
            <div id="local-map-${i}" class="local-map"></div>
            <p><strong>Regional Context:</strong> ${eq.history_count} historical earthquakes (M5.0+) within 10° since 1970.</p>

            <div style="text-align: right; margin-bottom: 15px;">
                 <a href="${eq.usgs_url}" target="_blank" class="btn" style="color: #fff !important; font-weight: bold; background-color: #3498db; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Full USGS Event Page</a>
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

        const localMap = L.map(`local-map-${i}`).setView([eq.lat, eq.lon], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(localMap);
        L.geoJSON(plates, { style: { color: 'orange', weight: 2 } }).addTo(localMap);
        L.circleMarker([eq.lat, eq.lon], { radius: 10, color: '#d32f2f', fillColor: '#d32f2f', fillOpacity: 0.8 }).addTo(localMap);
        if (eq.history_geojson) {
            L.geoJSON(eq.history_geojson, {
                pointToLayer: (f, latlng) => (f.id === eq.id) ? null : L.circleMarker(latlng, { radius: 4, color: '#2980b9', weight: 1, fillOpacity: 0.3 }),
                onEachFeature: (f, layer) => layer.bindPopup(`M${f.properties.mag} - ${new Date(f.properties.time).getFullYear()}`)
            }).addTo(localMap);
        }
    });
}
