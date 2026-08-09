"""
Outlier detection module for GitHub issue resolution times.

Implements IQR-based outlier detection on log-transformed resolution times
and generates a detailed report.
"""

import json
import logging
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import from project utilities
from utils.config import get_config, get_path


def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned issues dataset.
    
    Returns:
        DataFrame with cleaned issue data including resolution_time_hours.
        
    Raises:
        FileNotFoundError: If the cleaned dataset does not exist.
    """
    config = get_config()
    data_path = get_path(config, "processed_cleaned_issues")
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}")
    
    logging.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Ensure resolution_time_hours is numeric
    if 'resolution_time_hours' not in df.columns:
        raise ValueError("Cleaned dataset missing 'resolution_time_hours' column")
    
    df['resolution_time_hours'] = pd.to_numeric(
        df['resolution_time_hours'], errors='coerce'
    )
    
    return df


def detect_outliers_iqr(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect extreme outliers using the IQR method on log-transformed resolution times.
    
    The IQR method identifies outliers as values > Q3 + 1.5 * IQR.
    This is applied to log-transformed resolution times to handle the 
    skewed distribution of issue resolution times.
    
    Args:
        df: DataFrame with 'resolution_time_hours' column.
        
    Returns:
        Tuple of (DataFrame with outlier flags, Dict with outlier statistics)
    """
    # Filter out non-positive values for log transformation
    valid_df = df[df['resolution_time_hours'] > 0].copy()
    invalid_count = len(df) - len(valid_df)
    
    if len(valid_df) == 0:
        logging.warning("No valid resolution times found for outlier detection")
        return df, {
            "total_issues": len(df),
            "valid_issues": 0,
            "outlier_count": 0,
            "outlier_percentage": 0.0,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "log_lower_bound": None,
            "log_upper_bound": None,
            "invalid_count": invalid_count,
            "outliers": []
        }
    
    # Log-transform resolution times (add small epsilon to avoid log(0))
    # Since we filtered > 0, we can safely log
    log_times = np.log(valid_df['resolution_time_hours'])
    
    # Calculate Q1, Q3, and IQR
    q1 = np.percentile(log_times, 25)
    q3 = np.percentile(log_times, 75)
    iqr = q3 - q1
    
    # Calculate bounds for outlier detection
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Identify outliers
    outliers_mask = (log_times < lower_bound) | (log_times > upper_bound)
    
    # Create a copy to add outlier flag
    result_df = df.copy()
    result_df['is_outlier'] = False
    
    # Map outlier flags back to original dataframe
    # We need to match indices carefully
    valid_indices = valid_df.index
    outlier_indices = valid_df[outliers_mask].index
    
    result_df.loc[outlier_indices, 'is_outlier'] = True
    
    # Calculate statistics
    outlier_count = outlier_indices.shape[0]
    total_valid = len(valid_df)
    outlier_percentage = (outlier_count / total_valid * 100) if total_valid > 0 else 0.0
    
    # Prepare outlier details
    outlier_details = []
    if outlier_count > 0:
        outlier_df = valid_df[outliers_mask].copy()
        outlier_df['log_resolution_time'] = log_times[outliers_mask].values
        outlier_df['resolution_time_hours'] = outlier_df['resolution_time_hours']
        
        for _, row in outlier_df.head(100).iterrows():  # Limit to first 100 for report
            outlier_details.append({
                "issue_id": int(row.get('issue_id', 0)) if 'issue_id' in row else None,
                "repo": row.get('repo', 'unknown'),
                "resolution_time_hours": float(row['resolution_time_hours']),
                "log_resolution_time": float(row['log_resolution_time'])
            })
    
    stats = {
        "total_issues": len(df),
        "valid_issues": total_valid,
        "invalid_count": invalid_count,
        "outlier_count": outlier_count,
        "outlier_percentage": round(outlier_percentage, 2),
        "q1": round(float(q1), 4),
        "q3": round(float(q3), 4),
        "iqr": round(float(iqr), 4),
        "lower_bound": round(float(lower_bound), 4),
        "upper_bound": round(float(upper_bound), 4),
        "log_lower_bound": round(math.exp(lower_bound), 4),  # Back-transformed
        "log_upper_bound": round(math.exp(upper_bound), 4),  # Back-transformed
        "method": "IQR (Q3 + 1.5*IQR) on log-transformed data",
        "outliers": outlier_details
    }
    
    logging.info(f"Detected {outlier_count} outliers ({outlier_percentage:.2f}% of valid issues)")
    
    return result_df, stats


def save_report(stats: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the outlier detection report to JSON.
    
    Args:
        stats: Dictionary containing outlier statistics and details.
        output_path: Optional path to save the report. If None, uses config path.
        
    Returns:
        Path to the saved report file.
    """
    if output_path is None:
        config = get_config()
        output_path = get_path(config, "processed_outlier_report")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, default=str)
    
    logging.info(f"Outlier report saved to {output_path}")
    return str(output_path)


def main() -> None:
    """
    Main entry point for outlier detection analysis.
    
    Loads cleaned data, detects outliers using IQR method on log-transformed
    resolution times, and saves the report to data/processed/outlier_report.json.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/outlier_detection.log')
        ]
    )
    
    logging.info("Starting outlier detection analysis (Task T017)")
    
    try:
        # Load cleaned data
        df = load_cleaned_data()
        logging.info(f"Loaded {len(df)} issues from cleaned dataset")
        
        # Detect outliers
        result_df, stats = detect_outliers_iqr(df)
        
        # Save report
        report_path = save_report(stats)
        
        # Print summary
        print("\n" + "="*60)
        print("OUTLIER DETECTION SUMMARY (IQR Method on Log-Transformed Data)")
        print("="*60)
        print(f"Total issues analyzed: {stats['total_issues']}")
        print(f"Valid issues (positive resolution time): {stats['valid_issues']}")
        print(f"Invalid issues (non-positive): {stats['invalid_count']}")
        print(f"Outliers detected: {stats['outlier_count']}")
        print(f"Outlier percentage: {stats['outlier_percentage']}%")
        print(f"Q1 (log scale): {stats['q1']}")
        print(f"Q3 (log scale): {stats['q3']}")
        print(f"IQR (log scale): {stats['iqr']}")
        print(f"Upper bound (log scale): {stats['upper_bound']}")
        print(f"Upper bound (hours, back-transformed): {stats['log_upper_bound']}")
        print(f"\nReport saved to: {report_path}")
        print("="*60 + "\n")
        
        logging.info("Outlier detection completed successfully")
        
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {e}")
        print(f"ERROR: {e}")
        print("Please ensure the cleaned dataset exists at data/processed/cleaned_issues.csv")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during outlier detection: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
