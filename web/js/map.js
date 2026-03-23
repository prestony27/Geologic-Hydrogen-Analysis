// Initialize map centered on continental US
const map = L.map('map').setView([39.5, -98.35], 4);

// Base layer
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap, &copy; CARTO'
}).addTo(map);

// USGS Hydrogen Prospectivity Layer (Total Prospectivity)
const hydrogenLayer = L.esri.featureLayer({
    url: 'https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Naturally_Occurring_Geologic_Hydrogen_Prospectivity_Maps_10_22_2024_WFL1/FeatureServer/6',
    style: function(feature) {
        const score = feature.properties.gridcode_float || 0;
        return {
            fillColor: getHydrogenColor(score),
            fillOpacity: 0.85,
            color: '#555',
            weight: 0.3
        };
    }
}).addTo(map);

// Congressional Districts Layer (118th Congress)
const districtsLayer = L.esri.featureLayer({
    url: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0',
    style: {
        fillColor: 'transparent',
        fillOpacity: 0,
        color: '#333',
        weight: 1.5,
        dashArray: '4, 4'
    },
    onEachFeature: function(feature, layer) {
        const props = feature.properties;
        layer.bindPopup(`<strong>${props.BASENAME || props.NAME}</strong><br>State: ${props.STATE || 'N/A'}`);
    }
}).addTo(map);

// Color scale for hydrogen prospectivity (0-1) - matches USGS official colors
// Gradient: light green → cyan → dark blue
function getHydrogenColor(score) {
    // USGS color ramp (20 classes from their ArcGIS service)
    const colors = [
        [247, 252, 240], // 0.00-0.05
        [237, 248, 231], // 0.05-0.10
        [227, 244, 222], // 0.10-0.15
        [218, 240, 213], // 0.15-0.20
        [210, 237, 203], // 0.20-0.25
        [200, 233, 195], // 0.25-0.30
        [185, 227, 188], // 0.30-0.35
        [169, 221, 181], // 0.35-0.40
        [151, 214, 186], // 0.40-0.45
        [132, 207, 192], // 0.45-0.50
        [113, 198, 199], // 0.50-0.55
        [94, 188, 205],  // 0.55-0.60
        [76, 176, 209],  // 0.60-0.65
        [61, 160, 201],  // 0.65-0.70
        [46, 144, 192],  // 0.70-0.75
        [31, 128, 184],  // 0.75-0.80
        [17, 113, 176],  // 0.80-0.85
        [8, 97, 165],    // 0.85-0.90
        [8, 80, 147],    // 0.90-0.95
        [8, 64, 129]     // 0.95-1.00
    ];

    const index = Math.min(Math.floor(score * 20), 19);
    const [r, g, b] = colors[index];
    return `rgb(${r}, ${g}, ${b})`;
}

// Layer toggle controls
document.getElementById('toggle-hydrogen').addEventListener('change', function(e) {
    if (e.target.checked) {
        map.addLayer(hydrogenLayer);
    } else {
        map.removeLayer(hydrogenLayer);
    }
});

document.getElementById('toggle-districts').addEventListener('change', function(e) {
    if (e.target.checked) {
        map.addLayer(districtsLayer);
    } else {
        map.removeLayer(districtsLayer);
    }
});
