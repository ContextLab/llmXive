"""
Manifest updater for batch generation results.
Updates the global batch manifest with stratification summaries.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from code.src.utils.logging import log_metric

MANIFEST_PATH = Path("data/raw/global_batch_manifest.json")
SCHEMA_PATH = Path("contracts/manifest.schema.yaml")

def update_manifest(aggregated_data: Dict[str, Any], config: Dict[str, Any]):
    """
    Update the global batch manifest with generation results.
    Includes stratification summary and generation algorithm details.
    """
    logger = logging.getLogger(__name__)

    # Load existing manifest or create new one
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0",
            "generation_algorithm": {},
            "stratification_summary": {},
            "results": []
        }

    # Update generation algorithm info
    manifest["generation_algorithm"] = {
        "name": "batch_generator",
        "version": "1.0",
        "topology_classes": list(config.get("topology_targets", {}).keys()),
        "params": aggregated_data.get("summary", {})
    }

    # Update stratification summary
    stratification_params = config.get("stratification_params", {})
    bins = stratification_params.get("bins", [])
    target_counts = stratification_params.get("target_counts", {})

    # Count graphs per bin
    bin_counts = {}
    for result in aggregated_data.get("all_results", []):
        bin_name = result.get("clustering_bin", "unknown")
        bin_counts[bin_name] = bin_counts.get(bin_name, 0) + 1

    manifest["stratification_summary"] = {
        "bins": bins,
        "target_counts": target_counts,
        "actual_counts": bin_counts,
        "completion_status": check_stratification_completion(bin_counts, target_counts)
    }

    # Update results
    manifest["results"] = aggregated_data.get("all_results", [])
    manifest["summary"] = aggregated_data.get("summary", {})

    # Update timestamp
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()

    # Save manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Updated manifest at {MANIFEST_PATH}")

    # Log completion
    log_metric({
        "event_type": "simulation_end",
        "run_id": "manifest_update",
        "seed": config.get("global_seed", 0),
        "status": "success",
        "duration_seconds": 0.0
    })

    return manifest

def check_stratification_completion(actual_counts: Dict[str, int], target_counts: Dict[str, int]) -> str:
    """
    Check if stratification quotas are met.
    Returns 'complete', 'partial', or 'incomplete'.
    """
    if not target_counts:
        return "complete"

    complete_bins = 0
    total_bins = len(target_counts)

    for bin_name, target in target_counts.items():
        actual = actual_counts.get(bin_name, 0)
        if actual >= target:
            complete_bins += 1

    if complete_bins == total_bins:
        return "complete"
    elif complete_bins > 0:
        return "partial"
    else:
        return "incomplete"

def main():
    """
    Main entry point for manifest updater.
    """
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Update global batch manifest")
    parser.add_argument("--aggregated-data", type=str, required=True,
                      help="Path to aggregated results JSON")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                      help="Path to configuration file")
    args = parser.parse_args()

    # Load aggregated data
    with open(args.aggregated_data, 'r') as f:
        aggregated_data = json.load(f)

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Update manifest
    update_manifest(aggregated_data, config)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())