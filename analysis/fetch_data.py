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


def fetch_arcgis_layer(url: str, layer_id: int = None, max_records: int = 5000) -> gpd.GeoDataFrame:
    """Fetch a layer from an ArcGIS FeatureServer as a GeoDataFrame."""
    query_url = f"{url}/{layer_id}/query" if layer_id else f"{url}/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "resultRecordCount": max_records,
    }

    response = requests.get(query_url, params=params)
    response.raise_for_status()

    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def fetch_hydrogen_data(layer_id: int = 6) -> gpd.GeoDataFrame:
    """Fetch hydrogen prospectivity data."""
    print(f"Fetching hydrogen layer {layer_id}...")
    return fetch_arcgis_layer(HYDROGEN_SERVICE, layer_id)


def fetch_congressional_districts() -> gpd.GeoDataFrame:
    """Fetch congressional district boundaries."""
    print("Fetching congressional districts...")
    return fetch_arcgis_layer(DISTRICTS_SERVICE)


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
