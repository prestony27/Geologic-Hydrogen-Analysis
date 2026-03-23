# Geologic Hydrogen Analysis

An interactive web map visualizing USGS geologic hydrogen prospectivity data with congressional district overlays. Analyze which U.S. congressional districts have the highest potential for naturally occurring hydrogen resources.

## Features

- Interactive Leaflet map with hydrogen prospectivity layer
- Congressional district boundaries (118th Congress) overlay
- Click on any district to see:
  - District name and state
  - Current US Representative
  - Both US Senators for that state
- Toggle layers on/off
- Spatial analysis to calculate average prospectivity by district
- USGS official color scheme (green-cyan-blue gradient)

## Project Structure

```
Geologic Hydrogen Analysis/
├── analysis/
│   ├── fetch_data.py         # Downloads data from USGS & Census APIs
│   └── spatial_analysis.py   # Calculates prospectivity by district
├── web/
│   ├── index.html            # Map page
│   ├── css/style.css         # Styling
│   ├── js/map.js             # Leaflet map configuration
│   └── data/                 # GeoJSON files (hydrogen + districts)
├── data/                     # Analysis output (gitignored)
├── requirements.txt          # Python dependencies
└── README.md
```

## Installation

### Prerequisites
- Python 3.10+
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/prestony27/Geologic-Hydrogen-Analysis.git
   cd Geologic-Hydrogen-Analysis
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### View the Interactive Map

The map data is already included in `web/data/`. Simply start a local server:

```bash
cd web
python -m http.server 8000
```

Open http://localhost:8000 in your browser.

**Map interactions:**
- Pan and zoom with mouse/touchpad
- Click on a congressional district to see its representative and senators
- Toggle layers using the checkboxes in the top-right panel

### Refresh Data (Optional)

To download the latest data from USGS and Census APIs:

```bash
python analysis/fetch_data.py
```

This fetches ~90,000 hydrogen prospectivity polygons and 433 congressional districts, then processes them for optimal map performance.

### Run Spatial Analysis

Calculate average hydrogen prospectivity for each congressional district:

```bash
python analysis/spatial_analysis.py
```

Results are saved to `data/prospectivity_by_district.csv`.

**Top districts by hydrogen prospectivity:**
| State | District | Avg Prospectivity |
|-------|----------|-------------------|
| MT | District 2 | 0.67 |
| WA | District 2 | 0.50 |
| WA | District 1 | 0.48 |
| MT | District 1 | 0.45 |
| WA | District 10 | 0.44 |

## Data Sources

- **USGS Hydrogen Prospectivity Maps**: [ArcGIS FeatureServer](https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Naturally_Occurring_Geologic_Hydrogen_Prospectivity_Maps_10_22_2024_WFL1/FeatureServer)
- **USGS Data Release**: [ScienceBase](https://www.sciencebase.gov/catalog/item/671be1c2d34efed56210dded)
- **Congressional Districts**: [Census Bureau TIGER/Line](https://www2.census.gov/geo/tiger/GENZ2023/shp/)
- **Congressional Members**: [unitedstates/congress-legislators](https://github.com/unitedstates/congress-legislators) - Current representatives and senators (119th Congress)

### Available Hydrogen Layers

The USGS service includes multiple prospectivity layers:
- Total Prospectivity (combined score)
- Source: Serpentinization, Radiolysis, Deep/Mantle
- Reservoir potential
- Seal potential
- Known hydrogen occurrences

## Technical Details

### Performance Optimizations

- **Canvas renderer**: Uses Leaflet's Canvas renderer (`preferCanvas: true`) for better performance with large datasets
- **Polygon dissolution**: Adjacent polygons with identical values are merged (90,116 → 72 features), reducing file size from 46MB to 26MB
- **Disabled path simplification**: `smoothFactor: 0` prevents gaps between polygons at low zoom levels

### Click Detection

Since Canvas renderer doesn't detect clicks on transparent polygon fills, the map uses a custom ray-casting point-in-polygon algorithm to determine which district was clicked.

### Color Scheme

The map uses the official USGS 20-class color ramp:
- Low prospectivity: Light green `rgb(247, 252, 240)`
- Medium: Cyan `rgb(113, 198, 199)`
- High prospectivity: Dark blue `rgb(8, 64, 129)`

## Acknowledgments

- **U.S. Geological Survey (USGS)** - Hydrogen prospectivity data and methodology
- **U.S. Census Bureau** - Congressional district boundaries
- **@unitedstates project** - Congressional legislators data
- **Leaflet** - Open-source JavaScript mapping library
- **OpenStreetMap & CARTO** - Base map tiles
