import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import pandas as pd
import numpy as np

from config import get_path, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessing_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load preprocessing configuration from config.yaml or default settings."""
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()
    
    # Default configuration if not specified
    default_config = {
        "missing_threshold": 0.05,
        "imputation_strategy": "mean",
        "critical_columns": [
            "search_count", 
            "error_frequency", 
            "token_usage", 
            "turn_number", 
            "embedding_distance",
            "abstention_label"
        ]
    }
    
    # Merge with defaults
    for key, value in default_config.items():
        if key not in config.get("preprocessing", {}):
            config.setdefault("preprocessing", {})[key] = value
    
    return config.get("preprocessing", default_config)

def calculate_missing_statistics(df: pd.DataFrame, critical_columns: List[str]) -> Dict[str, Any]:
    """Calculate missing value statistics for the dataset."""
    stats = {}
    
    for col in critical_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            total_count = len(df)
            missing_ratio = missing_count / total_count if total_count > 0 else 0.0
            
            stats[col] = {
                "missing_count": int(missing_count),
                "total_count": int(total_count),
                "missing_ratio": float(missing_ratio),
                "is_critical": True
            }
        else:
            stats[col] = {
                "missing_count": 0,
                "total_count": 0,
                "missing_ratio": 1.0,
                "is_critical": True,
                "error": f"Column '{col}' not found in dataset"
            }
    
    # Calculate overall statistics
    total_critical_columns = len(critical_columns)
    critical_columns_with_data = sum(
        1 for col in critical_columns 
        if col in df.columns and df[col].notna().any()
    )
    
    overall_missing_ratio = sum(
        stats[col]["missing_ratio"] 
        for col in critical_columns 
        if col in stats
    ) / total_critical_columns if total_critical_columns > 0 else 0.0
    
    stats["_summary"] = {
        "total_critical_columns": total_critical_columns,
        "overall_missing_ratio": float(overall_missing_ratio),
        "critical_columns_with_data": critical_columns_with_data
    }
    
    return stats

def perform_mean_imputation(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    """Perform mean imputation for missing numeric variables."""
    df_imputed = df.copy()
    imputation_info = {}
    
    for col in numeric_columns:
        if col in df_imputed.columns:
            if df_imputed[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                mean_val = df_imputed[col].mean()
                
                if not np.isnan(mean_val):
                    imputed_count = df_imputed[col].isna().sum()
                    if imputed_count > 0:
                        df_imputed[col] = df_imputed[col].fillna(mean_val)
                        imputation_info[col] = {
                            "mean_value": float(mean_val),
                            "imputed_count": int(imputed_count)
                        }
                        logger.info(f"Imputed {imputed_count} missing values in '{col}' with mean {mean_val:.4f}")
                else:
                    logger.warning(f"Cannot compute mean for column '{col}' (all values are NaN or empty)")
        else:
            logger.warning(f"Column '{col}' not found for imputation")
    
    return df_imputed, imputation_info

def validate_dataset(df: pd.DataFrame, stats: Dict[str, Any], threshold: float) -> bool:
    """
    Validate the dataset against missing value threshold.
    Returns True if dataset is valid, False otherwise.
    """
    overall_ratio = stats.get("_summary", {}).get("overall_missing_ratio", 0.0)
    
    if overall_ratio > threshold:
        logger.error(f"Dataset validation FAILED: Overall missing ratio {overall_ratio:.4f} exceeds threshold {threshold}")
        return False
    
    # Check individual critical columns
    for col, col_stats in stats.items():
        if col.startswith("_"):
            continue
        
        if col_stats.get("is_critical", False):
            if col_stats.get("missing_ratio", 0.0) > threshold:
                logger.error(f"Critical column '{col}' has missing ratio {col_stats['missing_ratio']:.4f} > {threshold}")
                return False
            
            if "error" in col_stats:
                logger.error(f"Critical column '{col}' error: {col_stats['error']}")
                return False
    
    logger.info(f"Dataset validation PASSED: Overall missing ratio {overall_ratio:.4f} <= {threshold}")
    return True

def generate_validation_report(
    df: pd.DataFrame, 
    stats: Dict[str, Any], 
    threshold: float, 
    is_valid: bool,
    imputation_info: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Generate a comprehensive validation report."""
    report = {
        "validation_status": "PASSED" if is_valid else "FAILED",
        "threshold": threshold,
        "summary": stats.get("_summary", {}),
        "column_statistics": {
            k: v for k, v in stats.items() if not k.startswith("_")
        },
        "imputation_details": imputation_info or {},
        "dataset_info": {
            "total_records": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": list(df.columns)
        }
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Validation report saved to: {output_path}")
    
    return report

def main():
    """Main entry point for the preprocessing pipeline."""
    logger.info("Starting data preprocessing pipeline")
    
    # Load configuration
    config = load_preprocessing_config()
    threshold = config.get("missing_threshold", 0.05)
    critical_columns = config.get("critical_columns", [])
    
    # Define paths
    data_dir = get_path("data_processed")
    input_file = data_dir / "features.parquet"
    output_file = data_dir / "features_processed.parquet"
    report_file = get_path("data_raw") / "validation_report.json"
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        # Generate failure report
        failure_report = generate_validation_report(
            pd.DataFrame(),
            {"_summary": {"overall_missing_ratio": 1.0, "error": "Input file not found"}},
            threshold,
            False,
            output_path=report_file
        )
        sys.exit(1)
    
    # Load dataset
    try:
        df = pd.read_parquet(input_file)
        logger.info(f"Loaded dataset with {len(df)} records and {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        failure_report = generate_validation_report(
            pd.DataFrame(),
            {"_summary": {"overall_missing_ratio": 1.0, "error": str(e)}},
            threshold,
            False,
            output_path=report_file
        )
        sys.exit(1)
    
    # Calculate missing statistics
    stats = calculate_missing_statistics(df, critical_columns)
    logger.info(f"Missing statistics calculated")
    
    # Validate dataset BEFORE imputation
    is_valid = validate_dataset(df, stats, threshold)
    
    if not is_valid:
        logger.warning("Dataset validation FAILED (>5% missing critical data). Generating report and halting.")
        report = generate_validation_report(
            df, 
            stats, 
            threshold, 
            is_valid,
            output_path=report_file
        )
        logger.error("Halting execution due to excessive missing data. Please check the validation report.")
        sys.exit(1)
    
    # Perform mean imputation on numeric columns
    numeric_columns = [col for col in df.select_dtypes(include=[np.number]).columns if col in critical_columns]
    df_imputed, imputation_info = perform_mean_imputation(df, numeric_columns)
    
    # Re-calculate statistics after imputation to confirm
    stats_after = calculate_missing_statistics(df_imputed, critical_columns)
    is_valid_after = validate_dataset(df_imputed, stats_after, threshold)
    
    if not is_valid_after:
        logger.error("Post-imputation validation failed. Halting execution.")
        report = generate_validation_report(
            df_imputed, 
            stats_after, 
            threshold, 
            is_valid_after,
            imputation_info,
            output_path=report_file
        )
        sys.exit(1)
    
    # Generate final validation report
    report = generate_validation_report(
        df_imputed,
        stats_after,
        threshold,
        True,
        imputation_info,
        output_path=report_file
    )
    
    # Save processed dataset
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_imputed.to_parquet(output_file, index=False)
    logger.info(f"Processed dataset saved to: {output_file}")
    
    logger.info("Preprocessing pipeline completed successfully")
    return report

if __name__ == "__main__":
    main()
