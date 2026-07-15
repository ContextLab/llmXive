"""
Real Data Runner module.
This module provides the interface for running statistical tests on real datasets
and saving the results. It acts as a wrapper around the validator logic.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.analysis.validator import (
    run_ttest_on_dataset,
    run_anova_on_dataset,
    run_chi_squared_on_dataset,
    save_p_values_to_csv,
    download_dataset,
    prepare_data_for_ttest,
    prepare_data_for_anova,
    prepare_data_for_chi_squared
)

def run_validation_on_datasets() -> List[Dict[str, Any]]:
    """
    Orchestrates the running of tests on all configured real datasets.
    Returns a list of result dictionaries.
    """
    # Import validator logic here to avoid circular imports if any
    from code.analysis.validator import run_validation_on_datasets as validator_main
    return validator_main()

def save_p_values_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the results of real data tests to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)

def load_p_values_to_csv_safe(input_path: str) -> pd.DataFrame:
    """
    Safely loads p-values from a CSV file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
    return pd.read_csv(input_path)

def main():
    """Main entry point for running validation."""
    print("Running real data validation via real_data_runner...")
    results = run_validation_on_datasets()
    output_path = os.path.join('data', 'simulation', 'real_data_pvalues.csv')
    save_p_values_to_csv(results, output_path)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
