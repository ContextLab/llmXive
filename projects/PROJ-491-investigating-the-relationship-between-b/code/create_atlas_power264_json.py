import json
import os
from pathlib import Path
from nilearn.datasets import fetch_atlas_power_2011

def fetch_power264_coordinates():
    """
    Fetch Power 2011 atlas coordinates.
    Note: This uses nilearn's fetch_atlas_power_2011 which returns 264 nodes.
    """
    try:
        data = fetch_atlas_power_2011()
        # The function returns a dictionary.
        # 'rois' usually contains the coordinates.
        # We need to extract MNI coordinates.
        if hasattr(data, 'rois'):
            return data.rois
        # Fallback or specific handling if structure differs
        return data
    except Exception as e:
        print(f"Error fetching Power 2011 atlas: {e}")
        return None

def write_json_contract(coords, output_path: Path):
    """Write the coordinates to a JSON contract file."""
    data = {
        "atlas": "Power 2011 (264 nodes)",
        "space": "MNI",
        "nodes": coords.tolist() if hasattr(coords, 'tolist') else coords
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Written atlas contract to {output_path}")

def main():
    ensure_dir = Path("data/contracts")
    ensure_dir.mkdir(parents=True, exist_ok=True)
    output_path = ensure_dir / "atlas_power264.json"
    
    coords = fetch_power264_coordinates()
    if coords is not None:
        write_json_contract(coords, output_path)
    else:
        print("Failed to fetch coordinates.")

if __name__ == "__main__":
    main()
