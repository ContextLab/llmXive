"""
Residual Validation Module.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

from code.analysis import perform_residual_normality_validation, load_processed_data
from code.logging_config import log_operation

def load_regression_data() -> pd.DataFrame:
    """Loads data for regression validation."""
    return load_processed_data()

def run_validation_pipeline() -> Dict[str, Any]:
    """Runs residual validation."""
    df = load_regression_data()
    res = perform_residual_normality_validation(df)
    
    output_path = "data/processed/regression_diagnostics.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(res, f, indent=2)
    return res

def main():
    """Entry point."""
    try:
        run_validation_pipeline()
    except Exception as e:
        print(f"Validation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
