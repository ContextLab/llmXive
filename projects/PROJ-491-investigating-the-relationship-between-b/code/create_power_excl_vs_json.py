import json
import math
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories
from state_manager import update_state_artifact


def load_json(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(file_path, 'r') as f:
        return json.load(f)


def calculate_distance(coord1: List[float], coord2: List[float]) -> float:
    """
    Calculate Euclidean distance between two 3D coordinates.
    
    Args:
        coord1: First coordinate [x, y, z]
        coord2: Second coordinate [x, y, z]
        
    Returns:
        Euclidean distance between the two points
    """
    if len(coord1) != 3 or len(coord2) != 3:
        raise ValueError("Coordinates must be 3D lists/tuples")
    
    return math.sqrt(
        (coord1[0] - coord2[0]) ** 2 +
        (coord1[1] - coord2[1]) ** 2 +
        (coord1[2] - coord2[2]) ** 2
    )


def find_overlapping_nodes(
    power_nodes: List[Dict[str, Any]],
    vs_roi: Dict[str, Any],
    distance_threshold: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Identify Power 264 nodes that overlap with the Ventral Striatum ROI.
    
    Overlap is defined as being within a Euclidean distance threshold 
    (default 10mm) of the VS ROI center.
    
    Args:
        power_nodes: List of Power 264 node dictionaries with 'x', 'y', 'z' coordinates
        vs_roi: Ventral Striatum ROI definition containing center coordinates
        distance_threshold: Maximum distance (mm) to consider a node overlapping
        
    Returns:
        List of Power nodes that overlap with the VS ROI
    """
    # Extract VS center coordinates from the ROI definition
    # Expected format: {"center": [x, y, z], ...}
    if "center" not in vs_roi:
        raise ValueError("VS ROI must contain 'center' key with [x, y, z] coordinates")
    
    vs_center = vs_roi["center"]
    overlapping_nodes = []
    
    for node in power_nodes:
        if "x" not in node or "y" not in node or "z" not in node:
            continue
        
        node_coords = [node["x"], node["y"], node["z"]]
        distance = calculate_distance(node_coords, vs_center)
        
        if distance <= distance_threshold:
            # Add node info with distance for reference
            node_info = node.copy()
            node_info["distance_to_vs"] = round(distance, 2)
            overlapping_nodes.append(node_info)
    
    return overlapping_nodes


def write_exclusion_contract(
    overlapping_nodes: List[Dict[str, Any]],
    output_path: str,
    vs_roi_id: str = "ventral_striatum",
    distance_threshold: float = 10.0
) -> None:
    """
    Write the exclusion contract JSON file listing nodes to exclude.
    
    Args:
        overlapping_nodes: List of Power nodes overlapping with VS ROI
        output_path: Path to write the exclusion contract JSON
        vs_roi_id: Identifier for the VS ROI used in the exclusion
        distance_threshold: Distance threshold used for identification
    """
    # Create the exclusion contract structure
    exclusion_contract = {
        "description": "Power 264 nodes overlapping with Ventral Striatum ROI",
        "exclusion_reason": "Prevent double-dipping in VS analysis",
        "vs_roi_id": vs_roi_id,
        "distance_threshold_mm": distance_threshold,
        "excluded_nodes": overlapping_nodes,
        "excluded_node_ids": [node.get("id", i) for i, node in enumerate(overlapping_nodes)],
        "total_excluded": len(overlapping_nodes)
    }
    
    # Ensure output directory exists
    ensure_directories([output_path])
    
    # Write the contract to file
    with open(output_path, 'w') as f:
        json.dump(exclusion_contract, f, indent=2)


def main():
    """Main entry point for creating the Power264 exclusion contract."""
    # Define paths
    project_root = Path(__file__).parent.parent
    power_contract_path = project_root / "data" / "contracts" / "atlas_power264.json"
    vs_roi_path = project_root / "data" / "contracts" / "roi_ventral_striatum.json"
    output_path = project_root / "data" / "contracts" / "Power264_excl_vs_nodes.json"
    
    # Load source data
    print(f"Loading Power 264 atlas from: {power_contract_path}")
    power_data = load_json(str(power_contract_path))
    
    print(f"Loading Ventral Striatum ROI from: {vs_roi_path}")
    vs_roi_data = load_json(str(vs_roi_path))
    
    # Extract nodes list (handle different possible structures)
    if "nodes" in power_data:
        power_nodes = power_data["nodes"]
    elif "atlas" in power_data and "nodes" in power_data["atlas"]:
        power_nodes = power_data["atlas"]["nodes"]
    else:
        # Assume the entire file content is the nodes list or has a different structure
        # Try to find a list of dictionaries with coordinates
        if isinstance(power_data, list):
            power_nodes = power_data
        else:
            raise ValueError("Could not find 'nodes' list in Power 264 JSON")
    
    # Find overlapping nodes
    print(f"Identifying nodes within 10mm of VS ROI center...")
    overlapping_nodes = find_overlapping_nodes(
        power_nodes, 
        vs_roi_data, 
        distance_threshold=10.0
    )
    
    print(f"Found {len(overlapping_nodes)} nodes overlapping with VS ROI")
    
    # Write exclusion contract
    write_exclusion_contract(
        overlapping_nodes,
        str(output_path),
        vs_roi_id="ventral_striatum",
        distance_threshold=10.0
    )
    
    print(f"Exclusion contract written to: {output_path}")
    
    # Update state manager
    update_state_artifact(str(output_path))
    
    return overlapping_nodes


if __name__ == "__main__":
    main()
