import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import json
from scipy import stats
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

# Import from utils
from utils import (
    get_project_root_path,
    get_data_raw_path,
    get_data_processed_path,
    get_data_qc_path,
    ensure_directory,
    write_json_log,
    setup_logger
)

logger = setup_logger('02_preprocess')

def load_cognitive_raw_data() -> pd.DataFrame:
    """Load raw cognitive data from parquet file."""
    raw_path = get_data_raw_path() / "cognitive_data.parquet"
    if not raw_path.exists():
        logger.error(f"Raw cognitive data not found at {raw_path}. Run T012 first.")
        raise FileNotFoundError(f"Raw cognitive data not found at {raw_path}. Run T012 first.")
    
    logger.info(f"Loading raw cognitive data from {raw_path}")
    df = pd.read_parquet(raw_path)
    logger.info(f"Loaded {len(df)} rows of cognitive data")
    return df

def apply_mice_imputation(df: pd.DataFrame, columns: Optional[list] = None) -> pd.DataFrame:
    """Apply MICE (Multiple Imputation by Chained Equations) for missing values."""
    if columns is None:
        # Default to numeric columns
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only columns that exist in df
    columns = [col for col in columns if col in df.columns]
    
    if not columns:
        logger.warning("No numeric columns found for imputation.")
        return df

    logger.info(f"Applying MICE imputation to columns: {columns}")
    
    # Create a copy to avoid modifying the original
    df_imputed = df.copy()
    
    # Check if there are any missing values
    if df_imputed[columns].isnull().sum().sum() == 0:
        logger.info("No missing values found in specified columns.")
        return df_imputed

    # Initialize MICE imputer
    imputer = IterativeImputer(random_state=42, max_iter=10, tol=0.001)
    
    # Fit and transform the data
    imputed_values = imputer.fit_transform(df_imputed[columns])
    df_imputed[columns] = imputed_values
    
    logger.info("MICE imputation completed.")
    return df_imputed

def compute_z_scores(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Compute z-scores for a specific column."""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    logger.info(f"Computing z-scores for column: {column}")
    
    df_z = df.copy()
    mean_val = df_z[column].mean()
    std_val = df_z[column].std()
    
    if std_val == 0:
        logger.warning(f"Standard deviation is 0 for column {column}. Setting z-scores to 0.")
        df_z[f"{column}_z"] = 0
    else:
        df_z[f"{column}_z"] = (df_z[column] - mean_val) / std_val
    
    logger.info(f"Z-scores computed for column: {column}")
    return df_z

def filter_outliers_by_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> tuple[pd.DataFrame, int]:
    """
    Filter outliers based on z-score threshold.
    
    Returns:
        tuple: (filtered_df, count_of_removed_outliers)
    """
    z_col = f"{column}_z"
    if z_col not in df.columns:
        # If z-score column doesn't exist, compute it first
        df = compute_z_scores(df, column)
        z_col = f"{column}_z"
    
    logger.info(f"Filtering outliers with z-score threshold: {threshold} on column: {column}")
    
    # Identify outliers
    outlier_mask = np.abs(df[z_col]) > threshold
    removed_count = outlier_mask.sum()
    
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} outliers (z-score > {threshold}) from {column}")
        filtered_df = df[~outlier_mask].copy()
    else:
        logger.info("No outliers found based on z-score threshold.")
        filtered_df = df.copy()
    
    return filtered_df, int(removed_count)

def save_processed_data(df: pd.DataFrame, filename: str = "processed_cognitive_data.parquet") -> Path:
    """Save processed data to parquet file."""
    processed_dir = get_data_processed_path()
    ensure_directory(processed_dir)
    output_path = processed_dir / filename
    
    logger.info(f"Saving processed data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved: {len(df)} rows")
    return output_path

def attempt_merge_and_report_gap(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Attempt to merge microbiome and cognitive data.
    If merge fails (0 rows), trigger gap report logic.
    """
    logger.info("Attempting to merge microbiome and cognitive data...")
    
    # Determine merge keys
    # Assuming 'sample_id' in microbiome and 'participant_id' in cognitive
    # We need to find common IDs
    
    # Try to find common column names or create a mapping
    if 'sample_id' in microbiome_df.columns and 'participant_id' in cognitive_df.columns:
        merged = microbiome_df.merge(
            cognitive_df,
            left_on='sample_id',
            right_on='participant_id',
            how='inner'
        )
    elif 'sample_id' in microbiome_df.columns and 'sample_id' in cognitive_df.columns:
        merged = microbiome_df.merge(
            cognitive_df,
            on='sample_id',
            how='inner'
        )
    else:
        logger.error("No common merge keys found between datasets.")
        return None

    logger.info(f"Merge resulted in {len(merged)} rows.")
    
    if len(merged) == 0:
        logger.warning("Merge resulted in 0 rows. Data gap detected.")
        # Trigger gap report logic
        _trigger_gap_report(microbiome_df, cognitive_df)
        return None
    
    return merged

def _trigger_gap_report(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> None:
    """Trigger the gap report generation."""
    logger.info("Generating data gap report...")
    
    # Import gap report generator
    from code_07_gap_report import generate_gap_report as generate_gap_report_internal
    
    # Generate the report
    generate_gap_report_internal(
        failure_reason="No common participant IDs found between Qiita 10313 and UK Biobank/NHANES",
        affected_studies=["Qiita_10313", "UK_Biobank"], # Placeholder, should be dynamic
        output_path=get_data_processed_path() / "data_gap_report.json"
    )
    
    # Also generate markdown report
    from code_generate_gap_report_md import main as generate_md_main
    generate_md_main()

def write_filtering_log(
    total_samples: int,
    removed_outliers: int,
    threshold: float,
    output_path: Optional[Path] = None
) -> Path:
    """
    Write filtering log to JSON file.
    
    Args:
        total_samples: Total number of samples before filtering
        removed_outliers: Number of outliers removed
        threshold: Z-score threshold used
        output_path: Optional custom output path. Defaults to data/qc/filtering_log.json
    
    Returns:
        Path: Path to the written log file
    """
    if output_path is None:
        qc_dir = get_data_qc_path()
        ensure_directory(qc_dir)
        output_path = qc_dir / "filtering_log.json"
    
    log_data = {
        "total_samples": total_samples,
        "removed_outliers": removed_outliers,
        "threshold": threshold
    }
    
    logger.info(f"Writing filtering log to {output_path}")
    write_json_log(output_path, log_data)
    logger.info(f"Filtering log written: {json.dumps(log_data)}")
    
    return output_path

def main():
    """Main execution function for preprocessing."""
    logger.info("Starting preprocessing pipeline (T015: Outlier Filtering)")
    
    try:
        # 1. Load raw cognitive data
        cognitive_df = load_cognitive_raw_data()
        
        # 2. Apply MICE imputation
        cognitive_df = apply_mice_imputation(cognitive_df)
        
        # 3. Compute z-scores for cognitive scores
        # Assuming the main cognitive score column is named 'composite_score' or similar
        score_col = None
        for col in cognitive_df.columns:
            if 'score' in col.lower() or 'z' in col.lower():
                score_col = col
                break
        
        if score_col is None:
            # Default to first numeric column if no obvious score column
            numeric_cols = cognitive_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                score_col = numeric_cols[0]
                logger.warning(f"No obvious score column found. Using '{score_col}' as default.")
            else:
                logger.error("No numeric columns found in cognitive data.")
                sys.exit(1)
        
        cognitive_df = compute_z_scores(cognitive_df, score_col)
        
        # 4. Filter outliers (T015 logic)
        total_before = len(cognitive_df)
        cognitive_df, removed_count = filter_outliers_by_zscore(
            cognitive_df, 
            score_col, 
            threshold=3.0
        )
        total_after = len(cognitive_df)
        
        # 5. Write filtering log (T015 requirement)
        write_filtering_log(
            total_samples=total_before,
            removed_outliers=removed_count,
            threshold=3.0
        )
        
        # 6. Save processed data
        save_processed_data(cognitive_df)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        # If cognitive data is missing, we can't proceed with preprocessing
        # This is expected if T012 hasn't run yet
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
