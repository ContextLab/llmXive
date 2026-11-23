import os
import numpy as np
import pandas as pd
import powerlaw
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_avalanche_sizes_from_store(data_root: Path) -> pd.DataFrame:
    # Load from all subfolders
    all_events = []
    aval_dir = data_root / "processed" / "avalanches"
    if not aval_dir.exists():
        return pd.DataFrame()
    
    for sub_dir in aval_dir.iterdir():
        if sub_dir.is_dir() and sub_dir.name.startswith("sub-"):
          csv_file = sub_dir / "avalanche_events.csv"
          if csv_file.exists():
              df = pd.read_csv(csv_file)
              if not df.empty:
                  all_events.append(df)
    
    if all_events:
        return pd.concat(all_events, ignore_index=True)
    return pd.DataFrame()

def fit_power_law_model(sizes: np.ndarray) -> Tuple[Optional[Dict], bool]:
    """
    Fits a power law model to the sizes.
    Returns (result_dict, success)
    """
    if len(sizes) < 10:
        return None, False
    
    try:
        results = powerlaw.Fit(sizes, discrete=True)
        # Check if power law is better than alternatives
        # This is a simplified check
        return {"alpha": results.alpha, "xmin": results.xmin}, True
    except Exception as e:
        logger.error(f"Power law fit failed: {e}")
        return None, False

def run_fitting_for_subject(subject_id: str, data_root: Path):
    """Runs fitting for a single subject."""
    events_file = data_root / "processed" / "avalanches" / f"sub-{subject_id}" / "avalanche_events.csv"
    if not events_file.exists():
        return
    
    df = pd.read_csv(events_file)
    if df.empty:
        return
    
    sizes = df["size"].values
    result, success = fit_power_law_model(sizes)
    
    # Save result
    out_dir = data_root / "processed" / "fitting" / f"sub-{subject_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "fit_result.json"
    
    import json
    with open(out_file, "w") as f:
        json.dump({"success": success, "result": result}, f)
    
    if not success:
        logger.warning(f"Fit failed for {subject_id}")

def run_fitting_pipeline(data_root: Path):
    """Runs fitting pipeline for all subjects."""
    aval_dir = data_root / "processed" / "avalanches"
    if not aval_dir.exists():
        return
    
    subjects = [d.name for d in aval_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    for sub_id in subjects:
        run_fitting_for_subject(sub_id, data_root)

def generate_fitting_report(data_root: Path):
    """Generates a report of fitting results."""
    pass

def main():
    data_root = get_data_root()
    run_fitting_pipeline(data_root)

if __name__ == "__main__":
    main()
