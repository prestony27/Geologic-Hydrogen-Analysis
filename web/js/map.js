// Initialize map centered on continental US
// Using Canvas renderer for better performance with many features
const map = L.map('map', {
    preferCanvas: true
}).setView([39.5, -98.35], 4);

// Congress data lookup tables
let fipsToState = {};
let senatorsByState = {};   // "CO" -> [{name, party}, ...]
let repsByDistrict = {};    // "CO-4" -> {name, party}
let congressDataLoaded = false;

// Load FIPS mapping and legislators data
async function loadCongressData() {
    try {
        const [fipsResponse, legislatorsResponse] = await Promise.all([
            fetch('data/fips-states.json'),
            fetch('data/legislators-current.json')
        ]);

        fipsToState = await fipsResponse.json();
        const legislators = await legislatorsResponse.json();

        buildLegislatorLookups(legislators);
        congressDataLoaded = true;
        console.log('Congress data loaded:', Object.keys(senatorsByState).length, 'states,', Object.keys(repsByDistrict).length, 'districts');
    } catch (err) {
        console.error('Error loading congress data:', err);
    }
}

function buildLegislatorLookups(legislators) {
    const today = new Date().toISOString().split('T')[0];

    for (const leg of legislators) {
        const terms = leg.terms || [];
        // Get current term (last term that hasn't ended yet, or most recent)
        const currentTerm = terms.filter(t => t.end >= today).pop() || terms[terms.length - 1];

        if (!currentTerm) continue;

        const name = leg.name.official_full || `${leg.name.first} ${leg.name.last}`;
        const party = currentTerm.party;
        const state = currentTerm.state;

        const memberInfo = { name, party };

        if (currentTerm.type === 'sen') {
            if (!senatorsByState[state]) {
                senatorsByState[state] = [];
            }
            senatorsByState[state].push(memberInfo);
        } else if (currentTerm.type === 'rep') {
            const district = currentTerm.district;
            const key = `${state}-${district}`;
            repsByDistrict[key] = memberInfo;
        }
    }
}

function getPartyAbbreviation(party) {
    const abbrs = {
        'Democrat': 'D',
        'Republican': 'R',
        'Independent': 'I',
        'Libertarian': 'L'
    };
    return abbrs[party] || party?.charAt(0) || '?';
}

function formatMember(member) {
    const partyAbbr = getPartyAbbreviation(member.party);
    return `${member.name} (${partyAbbr})`;
}

function buildPopupContent(feature) {
    if (!congressDataLoaded) {
        return '<div class="popup-content"><em>Loading congress data...</em></div>';
    }

    const props = feature.properties;
    const stateFips = props.STATEFP || '';
    const districtCode = props.CD118FP || '';
    const districtName = props.NAMELSAD || 'District';

    // Get state info from FIPS
    const stateInfo = fipsToState[stateFips] || { abbr: '??', name: `State ${stateFips}` };

    // Convert district code to number (handles "04" -> 4, "00" -> 0)
    let districtNum = parseInt(districtCode, 10);

    // DC uses district code 98 in GeoJSON but 0 in legislators data
    if (stateInfo.abbr === 'DC' && districtNum === 98) {
        districtNum = 0;
    }

    const lookupKey = `${stateInfo.abbr}-${districtNum}`;

    // Look up legislators
    const rep = repsByDistrict[lookupKey];
    const senators = senatorsByState[stateInfo.abbr] || [];

    // Build HTML
    let html = `
        <div class="popup-content">
            <h3>${districtName}</h3>
            <p class="state-name">${stateInfo.name}</p>
            <hr>
            <div class="representative">
                <strong>Representative:</strong><br>
                ${rep ? formatMember(rep) : '<em>Vacant</em>'}
            </div>
            <div class="senators">
                <strong>Senators:</strong><br>
                ${senators.length > 0
                    ? senators.map(formatMember).join('<br>')
                    : '<em>Not found</em>'}
            </div>
        </div>
    `;

    return html;
}

// Load congress data on page load
loadCongressData();

// Base layer
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap, &copy; CARTO | Data: USGS, Census Bureau'
}).addTo(map);

// Layer groups
let hydrogenLayer = null;
let districtsLayer = null;

// Color scale for hydrogen prospectivity (0-1) - matches USGS official colors
// Gradient: light green → cyan → dark blue
function getHydrogenColor(score) {
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

// Style function for hydrogen layer (no stroke for seamless appearance)
function hydrogenStyle(feature) {
    const score = feature.properties.gridcode_float || 0;
    return {
        fillColor: getHydrogenColor(score),
        fillOpacity: 0.85,
        stroke: false,
        weight: 0
    };
}

// Style function for congressional districts
function districtStyle(feature) {
    return {
        fillColor: 'transparent',
        fillOpacity: 0,
        color: '#333',
        weight: 1.5,
        dashArray: '4, 4'
    };
}

// Point-in-polygon detection using ray-casting algorithm
function isPointInPolygon(latlng, layer) {
    const point = [latlng.lng, latlng.lat];
    const geom = layer.feature.geometry;

    // Handle both Polygon and MultiPolygon
    const polygons = geom.type === 'MultiPolygon'
        ? geom.coordinates
        : [geom.coordinates];

    for (const polygon of polygons) {
        if (raycast(point, polygon[0])) return true;
    }
    return false;
}

function raycast(point, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1];
        const xj = ring[j][0], yj = ring[j][1];
        if (((yi > point[1]) !== (yj > point[1])) &&
            (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi)) {
            inside = !inside;
        }
    }
    return inside;
}

// Load hydrogen prospectivity data from local GeoJSON
fetch('data/hydrogen_prospectivity.geojson')
    .then(response => response.json())
    .then(data => {
        hydrogenLayer = L.geoJSON(data, {
            style: hydrogenStyle,
            smoothFactor: 0  // Disable path simplification to prevent gaps at low zoom
        }).addTo(map);
        console.log(`Loaded ${data.features.length} hydrogen features`);
    })
    .catch(err => console.error('Error loading hydrogen data:', err));

// Load congressional districts from local GeoJSON
fetch('data/congressional_districts.geojson')
    .then(response => response.json())
    .then(data => {
        districtsLayer = L.geoJSON(data, {
            style: districtStyle,
            onEachFeature: function(feature, layer) {
                layer.bindPopup(() => buildPopupContent(feature));
            }
        }).addTo(map);

        districtsLayer.bringToFront();
        console.log(`Loaded ${data.features.length} congressional districts`);
    })
    .catch(err => console.error('Error loading district data:', err));

// Map click handler for district interaction (works with transparent fills)
map.on('click', function(e) {
    if (!districtsLayer) return;

    // Find district containing the clicked point
    districtsLayer.eachLayer(function(layer) {
        // Quick bounds check first, then precise point-in-polygon
        if (layer.getBounds().contains(e.latlng) && isPointInPolygon(e.latlng, layer)) {
            layer.openPopup(e.latlng);
        }
    });
});

// Layer toggle controls
document.getElementById('toggle-hydrogen').addEventListener('change', function(e) {
    if (hydrogenLayer) {
        if (e.target.checked) {
            map.addLayer(hydrogenLayer);
        } else {
            map.removeLayer(hydrogenLayer);
        }
    }
});

document.getElementById('toggle-districts').addEventListener('change', function(e) {
    if (districtsLayer) {
        if (e.target.checked) {
            map.addLayer(districtsLayer);
        } else {
            map.removeLayer(districtsLayer);
        }
    }
});
