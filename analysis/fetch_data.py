"""
Fetch hydrogen prospectivity and congressional district data from ArcGIS services.
"""

import requests
import geopandas as gpd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Service URLs
HYDROGEN_SERVICE = "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Naturally_Occurring_Geologic_Hydrogen_Prospectivity_Maps_10_22_2024_WFL1/FeatureServer"
DISTRICTS_SERVICE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0"

HYDROGEN_LAYERS = {
    6: "Total_Prospectivity",
    7: "Combined_Source",
    8: "Source_Serpentinization",
    9: "Source_Radiolysis",
    10: "Source_Deep",
    11: "Seal",
    12: "Reservoir",
}


def fetch_arcgis_layer(url: str, layer_id: int = None, max_records: int = 5000, use_geojson: bool = True) -> gpd.GeoDataFrame:
    """Fetch a layer from an ArcGIS FeatureServer/MapServer as a GeoDataFrame."""
    query_url = f"{url}/{layer_id}/query" if layer_id else f"{url}/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson" if use_geojson else "json",
        "resultRecordCount": max_records,
        "outSR": "4326",
    }

    response = requests.get(query_url, params=params)
    response.raise_for_status()
    data = response.json()

    if use_geojson and "features" in data:
        return gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
    elif "features" in data:
        # Esri JSON format - convert to GeoDataFrame
        from shapely.geometry import shape, Polygon, MultiPolygon
        features = []
        for feat in data["features"]:
            geom = feat.get("geometry", {})
            props = feat.get("attributes", {})
            if "rings" in geom:
                # Esri polygon format
                rings = geom["rings"]
                if len(rings) == 1:
                    poly = Polygon(rings[0])
                else:
                    poly = Polygon(rings[0], rings[1:])
                features.append({"geometry": poly, **props})
        return gpd.GeoDataFrame(features, crs="EPSG:4326", geometry="geometry")
    else:
        raise ValueError(f"Unexpected response format: {list(data.keys())}")


def fetch_hydrogen_data(layer_id: int = 6) -> gpd.GeoDataFrame:
    """Fetch hydrogen prospectivity data."""
    print(f"Fetching hydrogen layer {layer_id}...")
    return fetch_arcgis_layer(HYDROGEN_SERVICE, layer_id)


def fetch_congressional_districts() -> gpd.GeoDataFrame:
    """Fetch congressional district boundaries from Census Bureau."""
    print("Fetching congressional districts...")
    # Use Census Bureau cartographic boundary file (simpler, more reliable)
    url = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip"
    return gpd.read_file(url)


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # Fetch Total Prospectivity
    hydrogen_gdf = fetch_hydrogen_data(6)
    hydrogen_gdf.to_file(DATA_DIR / "hydrogen_prospectivity.geojson", driver="GeoJSON")
    print(f"Saved {len(hydrogen_gdf)} hydrogen features")

    # Fetch Congressional Districts
    districts_gdf = fetch_congressional_districts()
    districts_gdf.to_file(DATA_DIR / "congressional_districts.geojson", driver="GeoJSON")
    print(f"Saved {len(districts_gdf)} district features")


if __name__ == "__main__":
    main()
