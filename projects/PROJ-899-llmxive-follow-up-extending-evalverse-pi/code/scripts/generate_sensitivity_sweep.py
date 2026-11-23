"""
Script to generate T033 Sensitivity Sweep.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.config import get_processed_data_dir, get_data_root
from src.utils import get_logger, ensure_directories, write_csv

def load_dimension_results():
    """Load correlation results from T016."""
    path = os.path.join(get_processed_data_dir(), "correlations.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlations file not found at {path}")
    return pd.read_csv(path)

def main():
    logger = get_logger(__name__)
    logger.info("Generating Sensitivity Sweep (T033)")
    
    try:
        df = load_dimension_results()
        
        # Thresholds to sweep
        thresholds = [0.80, 0.85, 0.90]
        
        results = []
        for _, row in df.iterrows():
            dim = row['dimension']
            r_val = row['pearson_r']
            
            for t in thresholds:
                status = "feature-sufficient" if r_val >= t else "VLM-required"
                results.append({
                    "dimension": dim,
                    "threshold": t,
                    "status": status
                })
        
        df_res = pd.DataFrame(results)
        out_path = os.path.join(get_data_root(), "sensitivity_sweep_raw.csv")
        ensure_directories([out_path])
        write_csv(df_res, out_path)
        logger.info(f"Wrote sensitivity sweep to {out_path}")
        
    except Exception as e:
        logger.error(f"Error in sensitivity sweep: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
