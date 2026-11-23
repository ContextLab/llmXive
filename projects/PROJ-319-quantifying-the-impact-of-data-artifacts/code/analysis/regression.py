"""
Regression modeling for calibration functions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats

try:
    from code.config import get_project_root
except ImportError:
    # Fallback
    import sys
    from pathlib import Path
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    from config import get_project_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fit_calibration_models(root: Path):
    """
    Fit linear/polynomial models linking artifact intensity to bias.
    Output: data/processed/calibration_functions.json
    """
    noise_stats_file = root / "data" / "processed" / "noise_stats.csv"
    sat_stats_file = root / "data" / "processed" / "saturation_stats.csv"
    output_file = root / "data" / "processed" / "calibration_functions.json"
    
    models = {}
    
    # Load noise stats
    if noise_stats_file.exists():
        # Read CSV
        import csv
        with open(noise_stats_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if rows:
            # Use the aggregated slope/intercept from the regression
            # Assuming the regression output has one row summarizing the trend
            row = rows[0]
            slope = float(row["slope"])
            intercept = float(row["intercept"])
            
            # Zero-intercept constraint (T039): If intercept is small, force to 0?
            # Or model bias = slope * sigma + intercept.
            # For calibration: correction = - (slope * sigma + intercept)
            models["ellipticity_model"] = {
                "type": "linear",
                "parameters": {"slope": slope, "intercept": intercept},
                "source": "noise_stats.csv"
            }
    
    # Load saturation stats
    if sat_stats_file.exists():
        import csv
        with open(sat_stats_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if rows:
            row = rows[0]
            slope = float(row["slope"])
            intercept = float(row["intercept"])
            
            models["asymmetry_model"] = {
                "type": "linear",
                "parameters": {"slope": slope, "intercept": intercept},
                "source": "saturation_stats.csv"
            }
    
    with open(output_file, 'w') as f:
        json.dump(models, f, indent=2)
    
    logger.info(f"Calibration functions saved to {output_file}")

def main():
    """Main entry point."""
    root = get_project_root()
    fit_calibration_models(root)

if __name__ == "__main__":
    main()
