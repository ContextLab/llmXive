import os
import sys
import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_correlation_results(data_root: Path) -> pd.DataFrame:
    file = data_root / "results" / "correlation_report.csv"
    if file.exists():
        return pd.read_csv(file)
    return pd.DataFrame()

def load_fitting_results(data_root: Path):
    # Placeholder
    return {}

def load_sensitivity_results(data_root: Path):
    # Placeholder
    return {}

def format_associational_statement(corr: float, p_value: float) -> str:
    return f"A weak association was observed (r={corr:.2f}, p={p_value:.2f})."

def generate_executive_summary(data_root: Path) -> str:
    return "Executive summary placeholder."

def generate_detailed_results(data_root: Path) -> str:
    return "Detailed results placeholder."

def generate_report(data_root: Path):
    """Generates the final report."""
    # Check collinearity status
    collinearity_file = data_root / "results" / "collinearity_status.json"
    high_collinearity = False
    if collinearity_file.exists():
        with open(collinearity_file, "r") as f:
            status = json.load(f)
            high_collinearity = status.get("high_collinearity", False)
    
    if high_collinearity:
        logger.warning("High collinearity detected. Suppressing predictive claims.")
    
    report_content = generate_executive_summary(data_root) + "\n" + generate_detailed_results(data_root)
    
    # Validate for causal keywords
    causal_keywords = ["causes", "drives", "leads to", "determines"]
    for keyword in causal_keywords:
        if keyword in report_content.lower():
            raise RuntimeError(f"Causal keyword '{keyword}' detected in report. Rephrase required.")
    
    # Save report
    out_file = data_root / "results" / "final_report.md"
    with open(out_file, "w") as f:
        f.write(report_content)
    
    logger.info(f"Saved final report to {out_file}")

def main():
    data_root = get_data_root()
    generate_report(data_root)

if __name__ == "__main__":
    main()
