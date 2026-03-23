"""
Spatial analysis: Calculate hydrogen prospectivity by congressional district.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_data():
    """Load hydrogen and district GeoJSON files."""
    hydrogen = gpd.read_file(DATA_DIR / "hydrogen_prospectivity.geojson")
    districts = gpd.read_file(DATA_DIR / "congressional_districts.geojson")
    return hydrogen, districts


def calculate_prospectivity_by_district(hydrogen: gpd.GeoDataFrame, districts: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Calculate area-weighted average hydrogen prospectivity for each congressional district.
    """
    # Ensure same CRS
    hydrogen = hydrogen.to_crs("EPSG:5070")  # Albers Equal Area for accurate area calc
    districts = districts.to_crs("EPSG:5070")

    results = []

    for idx, district in districts.iterrows():
        district_geom = district.geometry

        # Find intersecting hydrogen polygons
        intersecting = hydrogen[hydrogen.intersects(district_geom)].copy()

        if len(intersecting) == 0:
            avg_score = 0
        else:
            # Calculate intersection areas
            intersecting["intersection"] = intersecting.geometry.intersection(district_geom)
            intersecting["intersection_area"] = intersecting["intersection"].area

            # Area-weighted average
            total_area = intersecting["intersection_area"].sum()
            if total_area > 0:
                avg_score = (
                    intersecting["gridcode_float"] * intersecting["intersection_area"]
                ).sum() / total_area
            else:
                avg_score = 0

        results.append({
            "district_name": district.get("BASENAME") or district.get("NAME", f"District {idx}"),
            "state": district.get("STATE", "Unknown"),
            "avg_prospectivity": round(avg_score, 4),
            "district_area_km2": round(district_geom.area / 1e6, 2),
        })

    return pd.DataFrame(results).sort_values("avg_prospectivity", ascending=False)


def main():
    print("Loading data...")
    hydrogen, districts = load_data()

    print(f"Analyzing {len(districts)} districts against {len(hydrogen)} hydrogen polygons...")
    results = calculate_prospectivity_by_district(hydrogen, districts)

    output_path = DATA_DIR / "prospectivity_by_district.csv"
    results.to_csv(output_path, index=False)
    print(f"\nSaved results to {output_path}")

    print("\nTop 10 Districts by Hydrogen Prospectivity:")
    print(results.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
