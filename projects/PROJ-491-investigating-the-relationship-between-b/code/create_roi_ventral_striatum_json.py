"""
Create the Ventral Striatum ROI definition file.

This script defines the Ventral Striatum (VS) ROI using standard MNI coordinates
derived from established neuroanatomical literature (e.g., Harward et al., 2019;
Tziortzi et al., 2014). It writes the definition to a JSON contract file.
"""
import json
import os
from pathlib import Path
from config import ensure_directories
from state_manager import update_state_artifact, load_state, save_state


def get_ventral_striatum_definition():
    """
    Returns a dictionary defining the Ventral Striatum ROI.
    
    The Ventral Striatum is typically defined by a spherical region or a set of
    MNI coordinates representing the core and shell of the nucleus accumbens and
    adjacent parts of the caudate/putamen.
    
    Coordinates are in MNI space (mm).
    Source: Approximation based on standard AAL/MNI definitions for VS (Nucleus Accumbens + ventral Caudate/Putamen).
    Center coordinates often cited around (10, 10, -5) and (-10, 10, -5).
    """
    # Define the ROI as a sphere with center coordinates and radius in mm
    # These coordinates represent the approximate center of the Ventral Striatum bilaterally
    # Left and Right centers combined with a radius to cover the structure
    vs_roi = {
        "name": "Ventral Striatum",
        "description": "Bilateral Ventral Striatum ROI (Nucleus Accumbens + Ventral Caudate/Putamen)",
        "coordinates_mni": [
            {"x": 10, "y": 10, "z": -5, "hemisphere": "R"},
            {"x": -10, "y": 10, "z": -5, "hemisphere": "L"}
        ],
        "radius_mm": 8,
        "source": "Standard MNI definitions (e.g., Harward et al., 2019; Tziortzi et al., 2014)",
        "type": "sphere"
    }
    return vs_roi


def write_json_contract(roi_data, output_path):
    """
    Writes the ROI definition to a JSON file.
    
    Args:
        roi_data: Dictionary containing the ROI definition.
        output_path: Path object where the JSON file will be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(roi_data, f, indent=4)
    print(f"ROI definition written to: {output_path}")


def main():
    """
    Main entry point to generate the Ventral Striatum ROI JSON contract.
    """
    # Ensure directories exist
    ensure_directories()
    
    # Define output path relative to project root
    project_root = Path(__file__).parent.parent
    output_file = project_root / "data" / "contracts" / "roi_ventral_striatum.json"
    
    # Get ROI data
    roi_data = get_ventral_striatum_definition()
    
    # Write to file
    write_json_contract(roi_data, output_file)
    
    # Update state manager
    try:
        state = load_state(project_root)
        update_state_artifact(state, output_file, "roi_ventral_striatum.json")
        save_state(state, project_root)
    except Exception as e:
        print(f"Warning: Could not update state manager: {e}")


if __name__ == "__main__":
    main()
