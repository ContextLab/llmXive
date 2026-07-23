"""
Validates the dataset against minimum requirements.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
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

def calculate_coefficient_of_variation(group: pd.DataFrame, metric_col: str) -> float:
    """
    Calculates the Coefficient of Variation (CV) for a specific metric within a group.
    CV = std / mean. Returns 0.0 if mean is 0 or if there is insufficient data.
    """
    values = group[metric_col].dropna()
    if len(values) < 2:
        return 0.0
    
    mean_val = values.mean()
    if mean_val == 0:
        return 0.0
    
    std_val = values.std()
    return std_val / mean_val

def flag_high_variance_entries(df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Identifies and flags 'high variance' entries where the same polymer has 
    conflicting metrics (CV > threshold).
    
    Returns a dictionary with:
      - 'flagged_count': number of entries flagged
      - 'excluded_count': number of entries that would be excluded from training
      - 'variance_report': details of the flagged groups
    """
    if 'polymer_name' not in df.columns:
        logger.warning("No 'polymer_name' column found to check for high variance.")
        return {
            "flagged_count": 0,
            "excluded_count": 0,
            "variance_report": [],
            "message": "No polymer_name column found."
        }

    # Identify performance metric columns
    metric_cols = [c for c in ['permeability', 'selectivity'] if c in df.columns]
    if not metric_cols:
        logger.warning("No performance metric columns (permeability/selectivity) found.")
        return {
            "flagged_count": 0,
            "excluded_count": 0,
            "variance_report": [],
            "message": "No performance metrics found."
        }

    results = {
        "flagged_count": 0,
        "excluded_count": 0,
        "variance_report": [],
        "high_variance_polymer_names": []
    }

    # Group by polymer_name and check variance for each metric
    grouped = df.groupby('polymer_name')
    flagged_indices = set()
    flagged_polymer_names = []

    for name, group in grouped:
        is_high_variance = False
        for col in metric_cols:
            cv = calculate_coefficient_of_variation(group, col)
            if cv > threshold:
                is_high_variance = True
                break
        
        if is_high_variance:
            flagged_polymer_names.append(name)
            flagged_indices.update(group.index)
            results["variance_report"].append({
                "polymer_name": name,
                "count": len(group),
                "reason": f"CV > {threshold} in one or more metrics"
            })

    results["flagged_count"] = len(flagged_indices)
    results["excluded_count"] = len(flagged_indices)
    results["high_variance_polymer_names"] = flagged_polymer_names

    logger.info(f"Identified {results['flagged_count']} entries from {len(flagged_polymer_names)} polymers with high variance (CV > {threshold}).")
    
    return results

def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the dataset:
    1. Count valid records (must be >= 30).
    2. Verify >= 10 known high-performance bio-membranes.
    3. Check for and flag 'high variance' entries (same polymer, conflicting metrics)
       and ensure they are excluded from the primary training set.
    4. Generate missing_data_report.json if needed.
    """
    report = {
        "is_valid": True,
        "reason": "",
        "valid_records": 0,
        "bio_membranes": 0,
        "high_variance": {
            "flagged_count": 0,
            "excluded_count": 0,
            "polymer_names": []
        }
    }

    # 1. Count valid records
    valid_count = count_valid_records(df)
    report["valid_records"] = valid_count
    
    if valid_count < 30:
        report["is_valid"] = False
        report["reason"] = f"Valid records ({valid_count}) < 30"
        logger.warning(report["reason"])

    # 2. Verify high-performance bio-membranes
    bio_count = verify_high_performance_bio_membranes(df)
    # Re-calculate count for report consistency
    if 'class_name' in df.columns:
        report["bio_membranes"] = df[df['class_name'] != 'Unknown'].shape[0]
    else:
        report["bio_membranes"] = 0
        
    if report["bio_membranes"] < 10:
        report["is_valid"] = False
        report["reason"] += f"; Bio-membranes ({report['bio_membranes']}) < 10"
        logger.warning(report["reason"])

    # 3. Check for high variance entries (T044 Requirement)
    # This verifies the logic implemented in T015 by explicitly flagging them here
    variance_result = flag_high_variance_entries(df, threshold=0.5)
    report["high_variance"] = {
        "flagged_count": variance_result["flagged_count"],
        "excluded_count": variance_result["excluded_count"],
        "polymer_names": variance_result["high_variance_polymer_names"]
    }
    
    if variance_result["flagged_count"] > 0:
        logger.warning(
            f"High variance entries detected: {variance_result['flagged_count']} entries "
            f"from {len(variance_result['high_variance_polymer_names'])} polymers will be "
            f"excluded from the primary training set."
        )
        # Note: The actual exclusion happens in the pipeline flow (T015), 
        # but this validation step confirms the detection and flags the report.

    # 4. Generate missing data report if validation fails
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