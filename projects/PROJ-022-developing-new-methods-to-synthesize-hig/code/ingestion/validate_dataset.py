"""
Validates the dataset against minimum requirements.
"""
import os
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def count_valid_records(df: pd.DataFrame) -> int:
    """Counts records with at least one valid performance metric."""
    if 'permeability' in df.columns:
        valid = df['permeability'].notna()
    elif 'selectivity' in df.columns:
        valid = df['selectivity'].notna()
    else:
        valid = pd.Series([False] * len(df))
    return valid.sum()

def verify_high_performance_bio_membranes(df: pd.DataFrame, threshold: int = 10) -> bool:
    """Verifies existence of >= 10 known high-performance bio-membranes."""
    # Assuming 'class_name' or a specific tag indicates bio-membranes
    # For now, we check if we have enough records with class_name != 'Unknown'
    if 'class_name' not in df.columns:
        return False
    
    bio_count = df[df['class_name'] != 'Unknown'].shape[0]
    return bio_count >= threshold

def generate_missing_data_report(df: pd.DataFrame, path: str):
    """Generates a JSON report of missing data."""
    report = {}
    for col in df.columns:
        missing = df[col].isnull().sum()
        total = len(df)
        if missing > 0:
            report[col] = {
                "missing_count": int(missing),
                "missing_ratio": float(missing / total)
            }
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the dataset:
    1. Count valid records (must be >= 30).
    2. Verify >= 10 known high-performance bio-membranes.
    3. Generate missing_data_report.json if needed.
    """
    report = {
        "is_valid": True,
        "reason": "",
        "valid_records": 0,
        "bio_membranes": 0
    }

    valid_count = count_valid_records(df)
    report["valid_records"] = valid_count
    
    if valid_count < 30:
        report["is_valid"] = False
        report["reason"] = f"Valid records ({valid_count}) < 30"
        logger.warning(report["reason"])

    bio_count = verify_high_performance_bio_membranes(df)
    report["bio_membranes"] = bio_count
    
    if not bio_count: # Assuming function returns boolean, but we need count for report
       # Re-calculate count for report
       if 'class_name' in df.columns:
           report["bio_membranes"] = df[df['class_name'] != 'Unknown'].shape[0]
       else:
           report["bio_membranes"] = 0
       
       if report["bio_membranes"] < 10:
           report["is_valid"] = False
           report["reason"] += f"; Bio-membranes ({report['bio_membranes']}) < 10"
           logger.warning(report["reason"])

    # Generate report if needed
    if not report["is_valid"]:
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        generate_missing_data_report(df, str(output_dir / "missing_data_report.json"))
        logger.info("Generated missing_data_report.json due to validation failure.")

    return report

def main():
    # Dummy test
    data = {
        'polymer_name': ['P1'] * 35,
        'permeability': [10.0] * 35,
        'class_name': ['Bio'] * 15 + ['Other'] * 20
    }
    df = pd.DataFrame(data)
    result = validate_dataset(df)
    print(result)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
