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
            fillOpacity: 0.6,
            color: '#333',
            weight: 0.5
        };
    }
}).addTo(map);

// Congressional Districts Layer (118th Congress)
const districtsLayer = L.esri.featureLayer({
    url: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0',
    style: {
        fillColor: 'transparent',
        fillOpacity: 0,
        color: '#e74c3c',
        weight: 2
    },
    onEachFeature: function(feature, layer) {
        const props = feature.properties;
        layer.bindPopup(`<strong>${props.BASENAME || props.NAME}</strong><br>State: ${props.STATE || 'N/A'}`);
    }
}).addTo(map);

// Color scale for hydrogen prospectivity (0-1)
function getHydrogenColor(score) {
    if (score > 0.8) return '#08519c';
    if (score > 0.6) return '#3182bd';
    if (score > 0.4) return '#6baed6';
    if (score > 0.2) return '#9ecae1';
    return '#c6dbef';
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
