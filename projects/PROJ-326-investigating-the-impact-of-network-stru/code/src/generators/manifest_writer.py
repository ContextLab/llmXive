"""
Manifest writing logic for global_batch_manifest.json.
Implements T018e: Write manifest with schema validation.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.utils.config import load_config
from code.src.analysis.schema import validate_simulation_results  # Reuse schema validation logic

# Output path as per tasks.md
MANIFEST_PATH = "data/raw/global_batch_manifest.json"

# Ensure data/raw directory exists
os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)

logger = logging.getLogger(__name__)

def validate_manifest_schema(manifest: Dict[str, Any]) -> bool:
    """
    Validate the manifest against the expected schema.
    
    Expected schema structure:
    {
        "global_batch_manifest": {
            "version": str,
            "generated_at": str (ISO 8601),
            "global_seed": int,
            "topology_classes": [
                {
                    "class_name": str,
                    "graphs": [
                        {
                            "graph_id": int,
                            "parameters": dict,
                            "metrics": {
                                "clustering_coefficient": float,
                                "average_path_length": float,
                                "degree_distribution": dict
                            },
                            "is_connected": bool
                        }
                    ],
                    "success_count": int,
                    "total_attempts": int
                }
            ],
            "stratification_summary": {
                "bins": list,
                "target_counts": dict,
                "actual_counts": dict,
                "tolerance": float
            },
            "generation_algorithm": str
        }
    }
    """
    required_keys = ["version", "generated_at", "global_seed", "topology_classes", "stratification_summary", "generation_algorithm"]
    
    if not all(key in manifest for key in required_keys):
        missing = [k for k in required_keys if k not in manifest]
        logger.error(f"Manifest missing required keys: {missing}")
        return False
    
    # Validate topology_classes structure
    if not isinstance(manifest["topology_classes"], list):
        logger.error("topology_classes must be a list")
        return False
    
    for topo_class in manifest["topology_classes"]:
        if not all(k in topo_class for k in ["class_name", "graphs", "success_count", "total_attempts"]):
            logger.error(f"Invalid topology class structure: {topo_class}")
            return False
        
        if not isinstance(topo_class["graphs"], list):
            logger.error(f"graphs must be a list in class {topo_class['class_name']}")
            return False
        
        for graph in topo_class["graphs"]:
            if not all(k in graph for k in ["graph_id", "parameters", "metrics", "is_connected"]):
                logger.error(f"Invalid graph structure: {graph}")
                return False
    
    # Validate stratification_summary
    strat = manifest["stratification_summary"]
    if not all(k in strat for k in ["bins", "target_counts", "actual_counts", "tolerance"]):
        logger.error(f"Invalid stratification_summary structure: {strat}")
        return False
    
    return True

def write_manifest(
    topology_classes: List[Dict[str, Any]],
    stratification_summary: Dict[str, Any],
    generation_algorithm: str,
    global_seed: int,
    version: str = "1.0.0"
) -> str:
    """
    Write the global batch manifest to disk.
    
    Args:
        topology_classes: List of topology class results
        stratification_summary: Summary of stratification bins and counts
        generation_algorithm: Name of the generation algorithm used
        global_seed: The global random seed used
        version: Manifest version string
    
    Returns:
        Path to the written manifest file
    """
    manifest = {
        "global_batch_manifest": {
            "version": version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "global_seed": global_seed,
            "topology_classes": topology_classes,
            "stratification_summary": stratification_summary,
            "generation_algorithm": generation_algorithm
        }
    }
    
    if not validate_manifest_schema(manifest["global_batch_manifest"]):
        raise ValueError("Manifest schema validation failed")
    
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest written to {MANIFEST_PATH}")
    return MANIFEST_PATH

def main():
    """
    Main entry point for manifest writing.
    This function is called by the batch_runner to finalize the manifest.
    """
    config = load_config()
    seed = config.get("global_seed", 42)
    
    # Example data - in real usage, this would come from batch_runner aggregation
    # This is a placeholder to demonstrate the function works
    topology_classes = [
        {
            "class_name": "erdos_renyi",
            "graphs": [
                {
                    "graph_id": 1,
                    "parameters": {"p": 0.1},
                    "metrics": {
                        "clustering_coefficient": 0.1,
                        "average_path_length": 3.5,
                        "degree_distribution": {"mean": 3.0}
                    },
                    "is_connected": True
                }
            ],
            "success_count": 1,
            "total_attempts": 1
        }
    ]
    
    stratification_summary = {
        "bins": [0.1, 0.2, 0.3, 0.4, 0.5],
        "target_counts": {"0.1": 10, "0.2": 10, "0.3": 10, "0.4": 10, "0.5": 10},
        "actual_counts": {"0.1": 1, "0.2": 0, "0.3": 0, "0.4": 0, "0.5": 0},
        "tolerance": 0.1
    }
    
    write_manifest(
        topology_classes=topology_classes,
        stratification_summary=stratification_summary,
        generation_algorithm="batch_generator_v1",
        global_seed=seed
    )

if __name__ == "__main__":
    main()
