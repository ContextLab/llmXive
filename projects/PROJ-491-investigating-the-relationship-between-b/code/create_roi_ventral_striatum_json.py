import json
import os
from pathlib import Path
from config import ensure_directories
from state_manager import update_state_artifact, load_state, save_state

def get_ventral_striatum_definition():
    """
    Define the Ventral Striatum ROI in MNI coordinates.
    Approximate center and radius or list of voxels.
    For this contract, we define a spherical ROI centered at MNI coordinates.
    """
    # Typical MNI coordinates for Ventral Striatum
    # Left: [-10, 12, -6], Right: [10, 12, -6]
    # We will define a combined ROI or two separate entries.
    # Here we define a list of centers for the VS ROI.
    return {
        "name": "Ventral Striatum",
        "mni_coords": [
            {"hemisphere": "left", "x": -10, "y": 12, "z": -6},
            {"hemisphere": "right", "x": 10, "y": 12, "z": -6}
        ],
        "radius_mm": 6,
        "description": "Ventral Striatum ROI for reward processing analysis"
    }

def write_json_contract(roi_def, output_path: Path):
    """Write the ROI definition to a JSON contract file."""
    with open(output_path, 'w') as f:
        json.dump(roi_def, f, indent=2)
    print(f"Written ROI contract to {output_path}")

def main():
    ensure_directories()
    output_path = Path("data/contracts/roi_ventral_striatum.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    roi_def = get_ventral_striatum_definition()
    write_json_contract(roi_def, output_path)
    
    # Update state
    update_state_artifact(output_path)

if __name__ == "__main__":
    main()