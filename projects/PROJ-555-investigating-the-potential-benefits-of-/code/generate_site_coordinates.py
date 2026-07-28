"""
Generates a CSV file containing paired site coordinates for ecotourism and control sites.
Includes metadata such as biome and protection status.
"""
import os
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories

# Define the study area parameters (Central America / Costa Rica region as a representative ecotourism hotspot)
# Bounding box: Lat [8, 12], Lon [-86, -82]
MIN_LAT = 8.0
MAX_LAT = 12.0
MIN_LON = -86.0
MAX_LON = -82.0

# Biomes relevant to the region
BIOMES = [
    "Tropical Wet Forest",
    "Tropical Moist Forest",
    "Tropical Dry Forest",
    "Cloud Forest"
]

# Protection statuses
PROTECTION_STATUSES = [
    "National Park",
    "Private Reserve",
    "Community Conservation Area",
    "Buffer Zone",
    "Unprotected"
]

def generate_site_pairs(count: int = 30) -> List[Dict[str, Any]]:
    """
    Generates a list of paired sites (one ecotourism, one control) with realistic coordinates.
    
    Args:
        count: Number of pairs to generate.
        
    Returns:
        List of dictionaries containing site details.
    """
    sites = []
    random.seed(42)  # Reproducibility

    for i in range(count):
        # Generate a base location for the pair
        base_lat = random.uniform(MIN_LAT, MAX_LAT)
        base_lon = random.uniform(MIN_LON, MAX_LON)
        
        # Select biome and protection status for the pair context
        biome = random.choice(BIOMES)
        # Ecotourism sites are more likely to be protected or in buffer zones
        eco_protection = random.choice(["National Park", "Private Reserve", "Community Conservation Area", "Buffer Zone"])
        # Control sites are more likely to be unprotected or buffer zones
        control_protection = random.choice(["Buffer Zone", "Unprotected", "Community Conservation Area"])

        # Ecotourism Site (slightly offset)
        eco_lat = base_lat + random.uniform(-0.05, 0.05)
        eco_lon = base_lon + random.uniform(-0.05, 0.05)
        
        # Ensure within bounds
        eco_lat = max(MIN_LAT, min(MAX_LAT, eco_lat))
        eco_lon = max(MIN_LON, min(MAX_LON, eco_lon))

        # Control Site (offset in a different direction, ensuring > 5km distance approx)
        # We want them to be distinct but in the same biome context
        ctrl_lat = base_lat + random.uniform(0.1, 0.3) # Offset significantly
        ctrl_lon = base_lon + random.uniform(-0.1, 0.1)
        
        ctrl_lat = max(MIN_LAT, min(MAX_LAT, ctrl_lat))
        ctrl_lon = max(MIN_LON, min(MAX_LON, ctrl_lon))

        sites.append({
            "site_id": f"ECO-{i:03d}",
            "site_type": "ecotourism",
            "latitude": round(eco_lat, 6),
            "longitude": round(eco_lon, 6),
            "biome": biome,
            "protection_status": eco_protection,
            "pair_id": f"PAIR-{i:03d}"
        })

        sites.append({
            "site_id": f"CTRL-{i:03d}",
            "site_type": "control",
            "latitude": round(ctrl_lat, 6),
            "longitude": round(ctrl_lon, 6),
            "biome": biome,
            "protection_status": control_protection,
            "pair_id": f"PAIR-{i:03d}"
        })

    return sites

def write_site_coordinates(sites: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the site list to a CSV file.
    
    Args:
        sites: List of site dictionaries.
        output_path: Path to the output CSV file.
    """
    if not sites:
        raise ValueError("No sites to write.")

    fieldnames = [
        "site_id",
        "site_type",
        "latitude",
        "longitude",
        "biome",
        "protection_status",
        "pair_id"
    ]

    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sites)

def main():
    """
    Main entry point to generate and save site coordinates.
    """
    ensure_directories()
    
    output_path = Path("data/raw/site_coordinates.csv")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating 30 pairs of sites (60 total)...")
    sites = generate_site_pairs(count=30)
    
    print(f"Writing to {output_path}...")
    write_site_coordinates(sites, output_path)
    
    print(f"Successfully generated {len(sites)} site records.")
    print(f"Output saved to: {output_path.resolve()}")

if __name__ == "__main__":
    main()
