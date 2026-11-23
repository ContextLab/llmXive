"""
Merge W=0 delocalized results with W>0 scaling fits.
Ensures `is_delocalized` flag is correctly set for W=0 entries.
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_w0_results(path: str) -> List[Dict[str, Any]]:
    """Load W=0 results from the specified path."""
    if not os.path.exists(path):
        logger.warning(f"W=0 results file not found at {path}. Returning empty list.")
        return []
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Ensure is_delocalized is set to True for all entries
    for entry in data:
        entry['is_delocalized'] = True
        # Ensure disorder_width is 0.0 if missing or None
        if 'disorder_width' not in entry or entry['disorder_width'] is None:
            entry['disorder_width'] = 0.0
        # Ensure xi is null or None for delocalized states to prevent log(0) later
        if 'xi' not in entry or entry['xi'] is None:
            entry['xi'] = None
        if 'uncertainty' not in entry or entry['uncertainty'] is None:
            entry['uncertainty'] = None
    
    return data

def load_scaling_fits(path: str) -> List[Dict[str, Any]]:
    """Load W>0 scaling fits from the specified path."""
    if not os.path.exists(path):
        logger.warning(f"Scaling fits file not found at {path}. Returning empty list.")
        return []
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Filter out any W=0 entries if they exist (shouldn't, but safety check)
    filtered_data = []
    for entry in data:
        w = entry.get('disorder_width', 0.0)
        if w > 0:
            # Ensure is_delocalized is False for W>0
            entry['is_delocalized'] = False
            filtered_data.append(entry)
        else:
            logger.warning(f"Found W=0 entry in scaling_fits.json: {entry}. Skipping.")
    
    return filtered_data

def merge_results(w0_results: List[Dict[str, Any]], scaling_fits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge W=0 and W>0 results into a single list."""
    merged = scaling_fits + w0_results
    logger.info(f"Merged {len(scaling_fits)} W>0 fits and {len(w0_results)} W=0 results.")
    return merged

def write_merged_results(merged: List[Dict[str, Any]], output_path: str):
    """Write the merged results to the output path."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)
    
    logger.info(f"Wrote merged results to {output_path}")

def main():
    """Main entry point for merging scaling results."""
    config = get_config()
    base_path = Path(config.get('DATA_PROCESSED', 'data/processed'))
    
    w0_path = base_path / 'w0_results.json'
    scaling_raw_path = base_path / 'pr_scaling_raw.json'
    output_path = base_path / 'scaling_fits.json'
    
    # Load inputs
    w0_data = load_w0_results(str(w0_path))
    scaling_data = load_scaling_fits(str(scaling_raw_path))
    
    # Merge
    merged = merge_results(w0_data, scaling_data)
    
    # Write output
    write_merged_results(merged, str(output_path))
    
    logger.info("Merge complete.")

if __name__ == '__main__':
    main()
