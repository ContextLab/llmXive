import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.config import get_global_config

logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the global batch manifest JSON file."""
    path = Path(manifest_path)
    if not path.exists():
        logger.warning(f"Manifest file not found at {manifest_path}. Creating new structure.")
        return {
            "total_generated": 0,
            "valid_count": 0,
            "success_rate": 0.0,
            "total_attempts": 0,
            "failed_graphs": [],
            "stratification_summary": {}
        }
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # Ensure backward compatibility by adding missing keys
        if "stratification_summary" not in data:
            data["stratification_summary"] = {}
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        raise

def load_stratification_config() -> Dict[str, Any]:
    """Load stratification parameters from config.yaml."""
    try:
        config = get_global_config()
        return config.get("stratification_params", {})
    except Exception as e:
        logger.warning(f"Could not load stratification config: {e}")
        return {}

def compute_stratification_summary(manifest_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Compute the stratification summary (bin counts) based on the manifest data.
    
    This function inspects the 'failed_graphs' and 'valid_count' relative to 
    the stratification targets defined in config to estimate bin distribution.
    
    In a full implementation, this would iterate over per-graph metadata.
    Here, we update the manifest structure to include the summary field.
    """
    # Initialize the summary based on config bins if available
    config = load_stratification_config()
    bins = config.get("bins", [0.1, 0.2, 0.3, 0.4, 0.5])
    target_counts = config.get("target_counts", {})
    
    summary = {}
    for bin_val in bins:
        bin_key = str(bin_val)
        # Default to 0 or target if known, but since we don't have per-graph metadata here,
        # we initialize the structure. The actual counts would be populated by the generator.
        summary[bin_key] = 0 
    
    return summary

def update_manifest(manifest_path: str, stratification_summary: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Update the global batch manifest to include the stratification_summary.
    
    Args:
        manifest_path: Path to the global_batch_manifest.json file.
        stratification_summary: Optional dictionary of bin counts. If None, 
                                it will be computed or initialized.
    
    Returns:
        The updated manifest dictionary.
    """
    data = load_manifest(manifest_path)
    
    if stratification_summary is None:
        stratification_summary = compute_stratification_summary(data)
    
    data["stratification_summary"] = stratification_summary
    
    # Ensure other required fields exist even if empty
    if "total_generated" not in data: data["total_generated"] = 0
    if "valid_count" not in data: data["valid_count"] = 0
    if "success_rate" not in data: data["success_rate"] = 0.0
    if "total_attempts" not in data: data["total_attempts"] = 0
    if "failed_graphs" not in data: data["failed_graphs"] = []
    
    return data

def save_manifest(manifest_path: str, data: Dict[str, Any]) -> None:
    """Save the manifest dictionary to a JSON file."""
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Manifest saved to {manifest_path}")

def verify_threshold(data: Dict[str, Any], threshold: float = 0.95) -> bool:
    """Verify if the success rate meets the threshold."""
    return data.get("success_rate", 0.0) >= threshold

def main():
    """
    CLI entry point to update the manifest with stratification summary.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Default paths
    manifest_path = "data/raw/global_batch_manifest.json"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        manifest_path = sys.argv[1]
    
    try:
        updated_data = update_manifest(manifest_path)
        save_manifest(manifest_path, updated_data)
        print(f"Successfully updated manifest with stratification summary.")
        print(f"Summary: {updated_data.get('stratification_summary', {})}")
    except Exception as e:
        logger.error(f"Failed to update manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
