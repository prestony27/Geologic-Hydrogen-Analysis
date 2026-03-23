"""
Fetch hydrogen prospectivity and congressional district data from ArcGIS services.
Downloads complete datasets with pagination for use in local web map.
"""

import requests
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
WEB_DATA_DIR = PROJECT_DIR / "web" / "data"

# Service URLs
HYDROGEN_SERVICE = "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Naturally_Occurring_Geologic_Hydrogen_Prospectivity_Maps_10_22_2024_WFL1/FeatureServer"

HYDROGEN_LAYERS = {
    6: "total_prospectivity",
    7: "combined_source",
    8: "source_serpentinization",
    9: "source_radiolysis",
    10: "source_deep",
    11: "seal",
    12: "reservoir",
}


def fetch_arcgis_layer_paginated(url: str, layer_id: int, batch_size: int = 2000) -> gpd.GeoDataFrame:
    """Fetch ALL features from an ArcGIS layer using pagination."""
    query_url = f"{url}/{layer_id}/query"
    all_features = []
    offset = 0

    print(f"  Fetching layer {layer_id} with pagination...")

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson",
            "resultRecordCount": batch_size,
            "resultOffset": offset,
            "outSR": "4326",
        }

        response = requests.get(query_url, params=params)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"    Fetched {len(all_features)} features...")

        # Check if there are more records
        if len(features) < batch_size:
            break

        offset += batch_size

    print(f"  Total: {len(all_features)} features")
    return gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")


def fetch_hydrogen_data(layer_id: int = 6) -> gpd.GeoDataFrame:
    """Fetch complete hydrogen prospectivity data with pagination."""
    layer_name = HYDROGEN_LAYERS.get(layer_id, f"layer_{layer_id}")
    print(f"Fetching hydrogen layer: {layer_name}")
    return fetch_arcgis_layer_paginated(HYDROGEN_SERVICE, layer_id)


def fetch_congressional_districts() -> gpd.GeoDataFrame:
    """Fetch congressional district boundaries from Census Bureau."""
    print("Fetching congressional districts from Census Bureau...")
    url = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip"
    gdf = gpd.read_file(url)
    print(f"  Total: {len(gdf)} districts")
    return gdf


def main():
    # Create output directories
    DATA_DIR.mkdir(exist_ok=True)
    WEB_DATA_DIR.mkdir(exist_ok=True)

    # Fetch Total Prospectivity (complete dataset)
    hydrogen_gdf = fetch_hydrogen_data(6)

    # Save to both locations
    hydrogen_gdf.to_file(DATA_DIR / "hydrogen_prospectivity.geojson", driver="GeoJSON")
    hydrogen_gdf.to_file(WEB_DATA_DIR / "hydrogen_prospectivity.geojson", driver="GeoJSON")
    print(f"Saved {len(hydrogen_gdf)} hydrogen features")

    # Fetch Congressional Districts
    districts_gdf = fetch_congressional_districts()

    # Keep only continental US + DC for cleaner map (exclude territories)
    continental_fips = [
        "01", "04", "05", "06", "08", "09", "10", "11", "12", "13",
        "16", "17", "18", "19", "20", "21", "22", "23", "24", "25",
        "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
        "36", "37", "38", "39", "40", "41", "42", "44", "45", "46",
        "47", "48", "49", "50", "51", "53", "54", "55", "56"
    ]
    districts_gdf = districts_gdf[districts_gdf["STATEFP"].isin(continental_fips)]

    # Save to both locations
    districts_gdf.to_file(DATA_DIR / "congressional_districts.geojson", driver="GeoJSON")
    districts_gdf.to_file(WEB_DATA_DIR / "congressional_districts.geojson", driver="GeoJSON")
    print(f"Saved {len(districts_gdf)} congressional districts (continental US)")


if __name__ == "__main__":
    main()
