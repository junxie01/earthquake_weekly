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
        document.getElementById('loading').innerHTML = `
            <p>Seismic analysis in progress or data unavailable.</p>
            <p style="font-size: 0.8em; color: #888;">Ensure you run 'python fetch_data.py' locally first or trigger GitHub Action.</p>
        `;
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
            radius: Math.max(f.properties.mag * 2, 2),
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
    document.getElementById('stat-total').innerText = data.total_count;
    document.getElementById('stat-m5').innerText = data.m5_plus;
    document.getElementById('stat-m6').innerText = data.m6_plus;
    document.getElementById('stat-update').innerText = new Date(data.update_time).toLocaleDateString();
}

function renderTopThree(data, plates) {
    const container = document.getElementById('top-earthquakes');
    data.top_3.forEach((eq, i) => {
        const card = document.createElement('div');
        card.className = 'eq-card';

        const reports = eq.usgs_reports;

        // Build Media/Image Gallery (Already Deduplicated in Backend)
        let mediaHTML = '';
        const reportTypes = ['shakemap', 'losspager', 'dyfi', 'focal_mechanism', 'moment_tensor'];
        reportTypes.forEach(type => {
            const report = reports[type];
            if (report && report.images && report.images.length > 0) {
                report.images.forEach(imgUrl => {
                    mediaHTML += `
                        <div class="media-item">
                            <img src="${imgUrl}" alt="${report.title}" onclick="window.open('${imgUrl}', '_blank')">
                            <div class="media-caption">${report.title} Visualization</div>
                        </div>
                    `;
                });
            }
        });

        // 1. USGS News Links
        let usgsNewsHTML = eq.public_info.length > 0
            ? eq.public_info.map(n => `<li><a href="${n.url}" target="_blank">${n.text}</a></li>`).join('')
            : '<li>No direct reports in USGS feed.</li>';

        // 2. Google News Links (NEW)
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

            <div class="media-grid">${mediaHTML || '<p style="padding: 20px; color: #666;">Waiting for USGS to process visual reports...</p>'}</div>

            <div class="report-section">
                <div class="report-box" style="border-left-color: #27ae60;">
                    <h4>Public Reporting & USGS Links</h4>
                    <ul>${usgsNewsHTML}</ul>
                </div>
                <div class="report-box" style="border-left-color: #f1c40f;">
                    <h4>Latest Google News</h4>
                    <ul>${googleNewsHTML}</ul>
                </div>
            </div>

            <div style="margin-top: 15px; text-align: center;">
                 <a href="${eq.usgs_url}" target="_blank" class="btn">View Full Scientific Event Page on USGS</a>
            </div>

            ${reports.tectonic_summary ? `
                <div style="margin-top: 15px;">
                    <strong>Tectonic Summary:</strong>
                    <div class="tectonic-summary">${reports.tectonic_summary}</div>
                </div>
            ` : ''}
        `;
        container.appendChild(card);

        // Map rendering
        const localMap = L.map(`local-map-${i}`).setView([eq.lat, eq.lon], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(localMap);
        L.geoJSON(plates, { style: { color: 'orange', weight: 2 } }).addTo(localMap);
        L.circleMarker([eq.lat, eq.lon], { radius: 10, color: '#d32f2f', fillColor: '#d32f2f', fillOpacity: 0.8 }).addTo(localMap);
        L.geoJSON(eq.history_geojson, {
            pointToLayer: (f, latlng) => {
                if (f.id === eq.id) return null;
                return L.circleMarker(latlng, { radius: 4, color: '#2980b9', weight: 1, fillOpacity: 0.3 });
            }
        }).addTo(localMap);
    });
}
