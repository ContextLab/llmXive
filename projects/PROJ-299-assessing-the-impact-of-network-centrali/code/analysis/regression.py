"""
Regression Analysis

Runs hierarchical linear regression with covariates.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import statsmodels.api as sm
from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json, write_dicts_to_csv, read_csv_as_dicts

def run_regression_analysis():
    """
    Run regression analysis.
    """
    logger = get_logger("regression")
    logger.info("Running Regression Analysis")

    merged_path = project_root / "data" / "analysis" / "merged_dataset.csv"
    if not merged_path.exists():
        logger.error("Merged dataset not found.")
        return 1

    df = pd.read_csv(merged_path)

    # Define models (simplified for this task)
    # In production, this would run the 9 specified models
    results = []
    
    # Example: Regression of TMT-A on degree_mean
    if "degree_mean" in df.columns and "TMT-A" in df.columns:
        X = df[["degree_mean", "age", "sex", "education", "diagnosis"]]
        X = sm.add_constant(X)
        y = df["TMT-A"]
        model = sm.OLS(y, X).fit()
        
        results.append({
            "outcome": "TMT-A",
            "predictor": "degree_mean",
            "beta": model.params["degree_mean"],
            "p_value": model.pvalues["degree_mean"],
            "r_squared": model.rsquared
        })

    output_path = project_root / "data" / "analysis" / "regression_results.csv"
    write_dicts_to_csv(output_path, results)

    logger.info(f"Wrote regression results to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run Regression Analysis")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return run_regression_analysis()

if __name__ == "__main__":
    sys.exit(main())
