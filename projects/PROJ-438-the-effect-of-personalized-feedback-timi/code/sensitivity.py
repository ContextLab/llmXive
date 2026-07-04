"""
Sensitivity Analysis for Feedback Timing Boundaries.

Implements FR-007: Sweeps the 2h and 48h boundaries by ±0.01h, ±0.05h, ±0.1h
to generate intermediate binned data for stability calculation.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config, get_config_value
from logging_config import get_logger, info, warning, error, debug
from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups

logger = get_logger(__name__)

# Define the offsets to sweep
OFFSETS_HOURS = [0.01, 0.05, 0.1]

def get_boundary_variations(base_lower: float, base_upper: float) -> List[Tuple[float, float]]:
    """
    Generate a list of (lower_bound, upper_bound) tuples by applying
    symmetric offsets to the base boundaries.
    Offsets applied: 0, +/-0.01, +/-0.05, +/-0.1
    """
    variations = []
    offsets = [0.0] + [x for x in OFFSETS_HOURS for x in (-x, x)]
    
    for offset in offsets:
        new_lower = base_lower + offset
        new_upper = base_upper + offset
        # Ensure logical ordering (lower < upper)
        if new_lower >= new_upper:
            warning(f"Skipping invalid boundary pair: lower={new_lower}, upper={new_upper}")
            continue
        variations.append((new_lower, new_upper))
    
    return variations

def run_sensitivity_analysis(
    input_path: Path,
    output_dir: Path,
    lower_bound: float = 2.0,
    upper_bound: float = 48.0
) -> Path:
    """
    Runs the sensitivity sweep.
    
    1. Loads learner intervals.
    2. Generates binned datasets for each boundary variation.
    3. Saves intermediate CSVs to `data/processed/sensitivity/`.
    
    Returns the path to the metadata file describing the runs.
    """
    info(f"Starting sensitivity analysis on {input_path}")
    info(f"Base boundaries: [{lower_bound}h, {upper_bound}h]")
    
    # Load data once
    df = load_learner_intervals(input_path)
    if df is None or df.empty:
        error("Input data is empty or missing. Cannot run sensitivity analysis.")
        raise ValueError("Input data empty")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    sensitivity_dir = output_dir / "sensitivity"
    sensitivity_dir.mkdir(parents=True, exist_ok=True)
    
    variations = get_boundary_variations(lower_bound, upper_bound)
    info(f"Generated {len(variations)} boundary variations to sweep.")
    
    metadata_rows = []
    
    for i, (lb, ub) in enumerate(variations):
        info(f"Processing variation {i+1}/{len(variations)}: [{lb}h, {ub}h]")
        
        # Re-bin the data with new boundaries
        # We reuse the binning logic but need to inject the new bounds.
        # The `bin_feedback_groups` function in bin_feedback_groups.py likely uses constants.
        # We will replicate the logic here to ensure dynamic bounds are used.
        
        # Logic from bin_feedback_groups (simplified for dynamic bounds):
        # "Immediate" < lb
        # "Delayed" >= lb and <= ub
        # "Variable" > ub
        
        def custom_bin(row):
            interval = row['median_interval_h']
            if interval < lb:
                return "Immediate"
            elif interval <= ub:
                return "Delayed"
            else:
                return "Variable"
        
        df_sweep = df.copy()
        df_sweep['feedback_group'] = df_sweep.apply(custom_bin, axis=1)
        
        # Output filename
        offset_str = f"{lb:.2f}_{ub:.2f}".replace(".", "_")
        output_filename = f"sensitivity_{offset_str}.csv"
        output_file = sensitivity_dir / output_filename
        
        df_sweep.to_csv(output_file, index=False)
        info(f"Saved intermediate data to {output_file}")
        
        # Record metadata
        metadata_rows.append({
            "run_id": i,
            "lower_bound_h": lb,
            "upper_bound_h": ub,
            "output_file": str(output_file),
            "n_records": len(df_sweep),
            "n_immediate": (df_sweep['feedback_group'] == "Immediate").sum(),
            "n_delayed": (df_sweep['feedback_group'] == "Delayed").sum(),
            "n_variable": (df_sweep['feedback_group'] == "Variable").sum()
        })
    
    # Save metadata summary
    metadata_df = pd.DataFrame(metadata_rows)
    metadata_path = sensitivity_dir / "sensitivity_run_metadata.csv"
    metadata_df.to_csv(metadata_path, index=False)
    info(f"Sensitivity sweep complete. Metadata saved to {metadata_path}")
    
    return metadata_path

def main():
    """Entry point for sensitivity analysis."""
    config = load_config()
    
    # Get paths from config
    input_file = Path(get_config_value(config, "paths.learner_intervals", "data/processed/learners_binned.csv"))
    output_base = Path(get_config_value(config, "paths.processed", "data/processed"))
    
    # Default boundaries from spec (2h, 48h)
    lower_bound = float(get_config_value(config, "sensitivity.lower_bound", 2.0))
    upper_bound = float(get_config_value(config, "sensitivity.upper_bound", 48.0))
    
    if not input_file.exists():
        error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    try:
        run_sensitivity_analysis(input_file, output_base, lower_bound, upper_bound)
        info("Sensitivity analysis completed successfully.")
    except Exception as e:
        error(f"Sensitivity analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()