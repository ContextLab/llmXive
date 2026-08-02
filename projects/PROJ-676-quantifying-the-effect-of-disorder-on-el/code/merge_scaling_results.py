import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def main():
    """Merge W>0 fits and W=0 delocalized results into scaling_fits.json."""
    # Load W>0 fits
    scaling_raw_path = Path("data/processed/pr_scaling_raw.json")
    w0_results_path = Path("data/processed/w0_results.json")
    
    w0_fits = []
    if w0_results_path.exists():
        with open(w0_results_path, 'r') as f:
            w0_data = json.load(f)
        if w0_data.get("is_delocalized"):
            w0_fits.append({
                "disorder_width": 0.0,
                "is_delocalized": True,
                "xi": None,
                "uncertainty": None
            })
        else:
            logger.warning("W=0 results indicate localized state (unexpected).")
    
    w_positive_fits = []
    if scaling_raw_path.exists():
        with open(scaling_raw_path, 'r') as f:
            w_positive_fits = json.load(f)
    
    # Merge
    merged = w0_fits + w_positive_fits
    
    # Write output
    output_path = Path("data/processed/scaling_fits.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=2)
    
    logger.info(f"Merged scaling fits written to {output_path}")

if __name__ == "__main__":
    main()
