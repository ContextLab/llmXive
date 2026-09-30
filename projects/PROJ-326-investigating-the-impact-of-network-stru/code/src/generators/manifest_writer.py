"""
Manifest writing logic for global batch generation.
Implements schema validation and writes to data/raw/global_batch_manifest.json.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from code.src.utils.config import load_config
from code.src.utils.logging import log_metric, init_logging

# Import schema validation if available, otherwise define locally
try:
    from code.src.generators.manifest_schema import validate_manifest_schema
except ImportError:
    # Fallback validation if schema module not yet created
    def validate_manifest_schema(data: Dict[str, Any]) -> bool:
        """Basic schema validation for the manifest."""
        required_keys = {"global_batch_id", "generation_algorithm", "stratification_summary", "graphs"}
        return required_keys.issubset(data.keys())

logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("data/raw/global_batch_manifest.json")

def load_batch_results(batch_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Load or aggregate batch results from individual graph metadata files.
    In a real pipeline, this would read from data/metadata/graph_<id>.json files.
    For this task, we assume batch_results are passed from the runner.
    """
    # If batch_results is empty, we would typically scan data/metadata/
    # For now, we trust the caller to pass aggregated results
    return batch_results

def build_manifest(
    batch_results: List[Dict[str, Any]],
    config: Dict[str, Any],
    global_batch_id: str = "batch_001"
) -> Dict[str, Any]:
    """
    Construct the global batch manifest according to the schema.
    """
    # Extract stratification info from config
    strat_params = config.get("stratification_params", {})
    bins = strat_params.get("bins", [])
    target_counts = strat_params.get("target_counts", {})
    tolerance = strat_params.get("tolerance", 0.0)

    # Build stratification summary
    stratification_summary = {
        "bins": bins,
        "target_counts": target_counts,
        "tolerance": tolerance,
        "actual_counts": {},
        "quota_fulfilled": True
    }

    # Count actual graphs per bin
    for graph_data in batch_results:
        # Assume graph_data has a "clustering_bin" or similar field
        # If not, we derive it from clustering_coefficient
        cc = graph_data.get("clustering_coefficient", 0.0)
        assigned_bin = None
        for i, bin_upper in enumerate(bins):
            if cc <= bin_upper:
                assigned_bin = bin_upper
                break
        if assigned_bin is None and bins:
            assigned_bin = bins[-1]
        elif not bins:
            assigned_bin = "default"

        stratification_summary["actual_counts"].setdefault(assigned_bin, 0)
        stratification_summary["actual_counts"][assigned_bin] += 1

    # Check quota fulfillment
    for bin_val, target in target_counts.items():
        actual = stratification_summary["actual_counts"].get(bin_val, 0)
        if abs(actual - target) > tolerance * target:
            stratification_summary["quota_fulfilled"] = False
            logger.warning(f"Quota not fulfilled for bin {bin_val}: target={target}, actual={actual}")

    manifest = {
        "global_batch_id": global_batch_id,
        "generation_algorithm": config.get("topology_targets", ["erdos_renyi", "watts_strogatz", "barabasi_albert"]),
        "stratification_summary": stratification_summary,
        "graphs": batch_results,
        "total_graphs": len(batch_results),
        "schema_version": "1.0"
    }

    return manifest

def validate_manifest(manifest: Dict[str, Any]) -> bool:
    """
    Validate the manifest against the schema.
    """
    return validate_manifest_schema(manifest)

def save_manifest(manifest: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Write the manifest to disk.
    """
    if path is None:
        path = MANIFEST_PATH

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Validate before saving
    if not validate_manifest(manifest):
        raise ValueError("Manifest failed schema validation")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    logger.info(f"Manifest saved to {path}")
    log_metric({
        "event_type": "graph_generated",
        "run_id": manifest.get("global_batch_id", "unknown"),
        "seed": 0,
        "status": "manifest_saved",
        "duration_seconds": 0.0
    })

def main(batch_results: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Main entry point for manifest writing.
    If batch_results are not provided, attempts to load from metadata directory.
    """
    # Initialize logging
    init_logging()
    logger.info("Starting manifest writing process")

    # Load config
    config = load_config()

    # If batch_results not provided, try to load from metadata
    if batch_results is None:
        metadata_dir = Path("data/metadata")
        if not metadata_dir.exists():
            logger.warning("Metadata directory not found. Creating empty manifest.")
            batch_results = []
        else:
            batch_results = []
            for meta_file in metadata_dir.glob("graph_*.json"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    batch_results.append(json.load(f))
            logger.info(f"Loaded {len(batch_results)} graph metadata files")

    # Build manifest
    manifest = build_manifest(batch_results, config)

    # Save manifest
    save_manifest(manifest)

    logger.info("Manifest writing completed successfully")

if __name__ == "__main__":
    main()
