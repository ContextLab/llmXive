"""
Module to identify Power 264 nodes overlapping with the Ventral Striatum (VS) ROI
and write a contract JSON file listing these nodes to prevent double-dipping.

Logic:
1. Load Power 264 node coordinates from data/contracts/atlas_power264.json
2. Load VS ROI definition from data/contracts/roi_ventral_striatum.json
3. Calculate Euclidean distance between each Power node and the VS center.
4. Identify nodes within a 10mm radius threshold (standard for fMRI ROI overlap).
5. Write the list of overlapping node IDs to data/contracts/Power264_excl_vs_nodes.json.
"""
import json
import math
from pathlib import Path

from config import ensure_directories
from state_manager import update_state_artifact


def load_json(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_distance(coord1: list, coord2: list) -> float:
    """Calculate Euclidean distance between two 3D coordinates."""
    if len(coord1) != 3 or len(coord2) != 3:
        raise ValueError("Coordinates must be 3D (x, y, z).")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(coord1, coord2)))


def find_overlapping_nodes(power_nodes: list, vs_center: list, threshold_mm: float = 10.0) -> list:
    """
    Identify Power nodes within the threshold distance of the VS center.
    
    Args:
        power_nodes: List of dicts with 'node_id' and 'coords'.
        vs_center: List of [x, y, z] coordinates for VS center.
        threshold_mm: Distance threshold in mm.
        
    Returns:
        List of node IDs that overlap with the VS ROI.
    """
    overlapping_ids = []
    for node in power_nodes:
        node_id = node["node_id"]
        node_coords = node["coords"]
        dist = calculate_distance(node_coords, vs_center)
        if dist <= threshold_mm:
            overlapping_ids.append(node_id)
    return overlapping_ids


def write_exclusion_contract(overlapping_ids: list, output_path: Path) -> None:
    """Write the list of overlapping node IDs to the exclusion contract JSON."""
    data = {
        "description": "Power 264 nodes overlapping with Ventral Striatum ROI (excluded to prevent double-dipping)",
        "threshold_mm": 10.0,
        "overlapping_node_ids": overlapping_ids,
        "count": len(overlapping_ids)
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> None:
    """Main entry point to generate the Power264_excl_vs_nodes.json contract."""
    ensure_directories()
    
    base_path = Path("data")
    contracts_dir = base_path / "contracts"
    
    power_file = contracts_dir / "atlas_power264.json"
    vs_file = contracts_dir / "roi_ventral_striatum.json"
    output_file = contracts_dir / "Power264_excl_vs_nodes.json"
    
    if not power_file.exists():
        raise FileNotFoundError(f"Power 264 atlas file not found: {power_file}")
    if not vs_file.exists():
        raise FileNotFoundError(f"VS ROI file not found: {vs_file}")
    
    # Load data
    power_data = load_json(power_file)
    vs_data = load_json(vs_file)
    
    # Extract coordinates
    # Power data structure: list of nodes with 'node_id' and 'coords'
    power_nodes = power_data.get("nodes", [])
    if not power_nodes:
        raise ValueError("Power 264 atlas data contains no nodes.")
        
    # VS data structure: contains 'center' key with [x, y, z]
    vs_center = vs_data.get("center")
    if not vs_center or len(vs_center) != 3:
        raise ValueError("VS ROI definition missing valid 'center' coordinates.")
    
    # Find overlaps
    overlapping_ids = find_overlapping_nodes(power_nodes, vs_center, threshold_mm=10.0)
    
    # Write output
    write_exclusion_contract(overlapping_ids, output_file)
    
    # Update state
    update_state_artifact(str(output_file))
    
    print(f"Successfully identified {len(overlapping_ids)} overlapping nodes.")
    print(f"Exclusion contract written to: {output_file}")


if __name__ == "__main__":
    main()
