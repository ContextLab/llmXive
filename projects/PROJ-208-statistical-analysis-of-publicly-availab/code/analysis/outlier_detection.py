import json
import logging
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from utils.config import get_config

def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    data_path = Path(config["paths"]["processed"]) / "cleaned_issues.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run T011 first.")
    return pd.read_csv(data_path)

def detect_outliers_iqr(df: pd.DataFrame, column: str = "resolution_time_hours") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect outliers using the IQR method (Q3 + 1.5*IQR).
    
    Returns:
        Tuple of (df with outlier flags, stats dict)
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset. Available: {list(df.columns)}")
    
    # Filter out NaN values for calculation
    valid_data = df[column].dropna()
    
    if len(valid_data) == 0:
        logging.warning("No valid data to calculate IQR.")
        return df.assign(is_outlier=False), {"q1": None, "q3": None, "iqr": None, "upper_bound": None, "lower_bound": None, "outlier_count": 0}
    
    q1 = valid_data.quantile(0.25)
    q3 = valid_data.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Flag outliers
    is_outlier = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    stats = {
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "outlier_count": int(is_outlier.sum()),
        "total_count": len(df),
        "outlier_percentage": float((is_outlier.sum() / len(df)) * 100) if len(df) > 0 else 0.0
    }
    
    return df.assign(is_outlier=is_outlier), stats

def save_report(stats: Dict[str, Any], outliers_df: pd.DataFrame, output_path: Path) -> None:
    """Save the outlier report to JSON and the flagged dataframe to CSV."""
    report = {
        "method": "IQR (Q3 + 1.5*IQR)",
        "statistics": {
            "q1": stats["q1"],
            "q3": stats["q3"],
            "iqr": stats["iqr"],
            "lower_bound": stats["lower_bound"],
            "upper_bound": stats["upper_bound"],
            "outlier_count": stats["outlier_count"],
            "total_count": stats["total_count"],
            "outlier_percentage": stats["outlier_percentage"]
        },
        "outliers": []
    }
    
    # Extract outlier rows for the report
    outliers = outliers_df[outliers_df["is_outlier"]]
    for _, row in outliers.iterrows():
        report["outliers"].append({
            "issue_id": row.get("issue_id"),
            "repo": row.get("repo"),
            "resolution_time_hours": float(row["resolution_time_hours"]) if pd.notna(row["resolution_time_hours"]) else None
        })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Outlier report saved to {output_path}")

def main():
    """Main entry point for outlier detection."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    config = get_config()
    output_path = Path(config["paths"]["processed"]) / "outlier_report.json"
    
    try:
        df = load_cleaned_data(config)
        logging.info(f"Loaded {len(df)} issues for outlier detection.")
        
        flagged_df, stats = detect_outliers_iqr(df, "resolution_time_hours")
        
        logging.info(f"Detected {stats['outlier_count']} outliers ({stats['outlier_percentage']:.2f}%).")
        
        save_report(stats, flagged_df, output_path)
        
        return 0
    except Exception as e:
        logging.error(f"Failed to detect outliers: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
