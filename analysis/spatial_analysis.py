"""
Spatial analysis: Calculate hydrogen prospectivity by congressional district.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# State FIPS codes to names
STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI",
}


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

        state_fips = district.get("STATEFP", "")
        state = STATE_FIPS.get(state_fips, state_fips)
        district_name = district.get("NAMELSAD", f"District {idx}")

        results.append({
            "state": state,
            "district": district_name,
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
