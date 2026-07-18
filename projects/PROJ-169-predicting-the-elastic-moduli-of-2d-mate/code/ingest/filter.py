"""
Filtering logic for 2D materials and tensor validation.

This module implements the filtering step for User Story 1 (T013c).
It validates elastic tensors and filters for 2D materials, logging exclusion reasons.

WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT 
solve the Schrödinger equation or perform first-principles calculations.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import logging
from data_models.material_graph import MaterialGraph

LOGGER = logging.getLogger(__name__)

@dataclass
class FilterStats:
    total_parsed: int
    kept: int
    excluded: int
    exclusion_details: List[Dict[str, Any]]

def is_valid_6_component_tensor(graph: MaterialGraph) -> bool:
    """
    Check if the elastic tensor is valid and has 6 components (Voigt notation).
    Returns False if tensor is None, not an array, or doesn't have shape (6, 6).
    Logs the reason for exclusion if invalid.
    """
    if graph.target_moduli is None:
        LOGGER.warning(f"Excluding {graph.material_id}: Tensor is None")
        return False
    
    try:
        arr = np.array(graph.target_moduli)
        # Elastic tensor in Voigt notation is 6x6
        if arr.shape != (6, 6):
            LOGGER.warning(f"Excluding {graph.material_id}: Invalid tensor shape {arr.shape} (expected 6x6)")
            return False
        # Check for NaN or Inf
        if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
            LOGGER.warning(f"Excluding {graph.material_id}: Tensor contains NaN/Inf")
            return False
        return True
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Excluding {graph.material_id}: Could not convert tensor - {e}")
        return False

def is_2d_material(graph: MaterialGraph) -> bool:
    """
    Check if the material is 2D.
    
    Heuristics used:
    1. Check metadata flag 'is_2d' if present.
    2. Check 'family_id' for known 2D families (e.g., TMD, MXene, Graphene-like).
    3. If no structure data is available to check vacuum, we rely on the source 
       filtering (T013a) but verify via family_id naming conventions if possible.
    
    Returns False if explicitly marked as non-2D or if family_id suggests 3D bulk.
    Logs exclusion reasons for non-2D materials.
    """
    # Check explicit metadata flag if available
    if hasattr(graph, 'metadata') and graph.metadata:
        if graph.metadata.get('is_2d') is False:
            LOGGER.warning(f"Excluding {graph.material_id}: Explicitly marked as non-2D in metadata")
            return False
        
        # If explicitly marked 2D, accept
        if graph.metadata.get('is_2d') is True:
            return True

    # Fallback: Check family_id for known 2D patterns
    # This assumes the parser (T013b) has set family_id based on chemical prototype
    if hasattr(graph, 'family_id') and graph.family_id:
        family = str(graph.family_id).lower()
        # Common 2D material families
        known_2d_families = ['tmd', 'mxene', 'graphene', 'h-bn', 'mos2', 'ws2', 'moos2', 'wos2']
        if any(k in family for k in known_2d_families):
            return True
        
        # If family_id suggests a bulk 3D structure (e.g., contains 'bulk' or specific 3D prototypes)
        # We might want to exclude these, but without explicit 3D markers, we assume 2D if source was filtered
        # For safety, if we can't verify it's 2D and it's not explicitly marked, we exclude it
        # to ensure data hygiene (SC-001).
        # However, if the source (Materials Project elasticity dataset) was pre-filtered for 2D,
        # we might just accept it. Given the task requirement to "Filter for 2D materials",
        # we must be strict. If we can't confirm 2D, we exclude.
        LOGGER.warning(f"Excluding {graph.material_id}: Cannot verify 2D nature from family_id '{graph.family_id}'")
        return False

    # If no family_id and no metadata, we cannot confirm it is 2D.
    # Exclude to maintain data quality.
    LOGGER.warning(f"Excluding {graph.material_id}: Missing family_id and metadata to verify 2D nature")
    return False

def filter_graphs(graphs: List[MaterialGraph]) -> Tuple[List[MaterialGraph], FilterStats]:
    """
    Filter a list of MaterialGraphs for 2D materials and valid tensors.
    
    Logs exclusion reasons for every excluded entry.
    Returns (filtered_list, stats).
    """
    kept = []
    excluded = []
    
    for g in graphs:
        # Check tensor validity first
        if not is_valid_6_component_tensor(g):
            excluded.append({
                "material_id": g.material_id,
                "reason": "invalid_tensor",
                "details": "Tensor missing, wrong shape, or contains NaN/Inf"
            })
            continue
        
        # Check 2D nature
        if not is_2d_material(g):
            excluded.append({
                "material_id": g.material_id,
                "reason": "not_2d",
                "details": "Material does not meet 2D criteria"
            })
            continue
        
        kept.append(g)
    
    stats = FilterStats(
        total_parsed=len(graphs),
        kept=len(kept),
        excluded=len(excluded),
        exclusion_details=excluded
    )
    
    # Log summary
    LOGGER.info(f"Filtering complete: Kept {len(kept)}/{len(graphs)} materials. "
                f"Excluded {len(excluded)} due to invalid tensors or non-2D nature.")
    
    return kept, stats

def save_filter_stats(stats: FilterStats, path: Path):
    """Save filter statistics to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(stats), f, indent=2)
    LOGGER.info(f"Saved filter stats to {path}")

def main():
    """Entry point for testing filter logic (standalone execution)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter MaterialGraphs for 2D and valid tensors.")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON/Parquet containing graphs")
    parser.add_argument("--output", type=str, required=True, help="Path to output filtered graphs (JSON)")
    parser.add_argument("--stats", type=str, default="data/processed/filter_stats.json", help="Path to save filter stats")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load graphs (assuming JSON for simplicity in this standalone test)
    # In the real pipeline, this would come from parse_cif output or parquet
    graphs = []
    input_path = Path(args.input)
    
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            data = json.load(f)
            # Reconstruct MaterialGraph objects
            for item in data:
                g = MaterialGraph(
                    material_id=item['material_id'],
                    composition=item['composition'],
                    target_moduli=np.array(item['target_moduli']) if item.get('target_moduli') else None,
                    family_id=item.get('family_id'),
                    metadata=item.get('metadata', {}),
                    node_features=item.get('node_features'),
                    edge_features=item.get('edge_features')
                )
                graphs.append(g)
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}. Use .json for this test.")
    
    LOGGER.info(f"Loaded {len(graphs)} graphs from {args.input}")
    
    # Filter
    filtered_graphs, stats = filter_graphs(graphs)
    
    # Save stats
    save_filter_stats(stats, Path(args.stats))
    
    # Save filtered graphs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    filtered_data = []
    for g in filtered_graphs:
        filtered_data.append({
            "material_id": g.material_id,
            "composition": g.composition,
            "target_moduli": g.target_moduli.tolist() if g.target_moduli is not None else None,
            "family_id": g.family_id,
            "metadata": g.metadata,
            "node_features": g.node_features,
            "edge_features": g.edge_features
        })
    
    with open(output_path, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    LOGGER.info(f"Saved {len(filtered_graphs)} filtered graphs to {args.output}")

if __name__ == "__main__":
    main()