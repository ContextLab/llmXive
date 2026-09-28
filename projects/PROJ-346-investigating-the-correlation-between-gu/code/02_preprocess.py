import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Import local utilities ensuring compatibility with the API surface
# The utils.py file provides path helpers and logging setup
try:
    from utils import (
        get_project_root_path,
        get_data_raw_path,
        get_data_processed_path,
        get_data_qc_path,
        setup_logger,
        write_json_log
    )
except ImportError:
    # Fallback for execution context where script is run directly
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import (
        get_project_root_path,
        get_data_raw_path,
        get_data_processed_path,
        get_data_qc_path,
        setup_logger,
        write_json_log
    )

logger = setup_logger("preprocess")

def load_cognitive_raw_data():
    """Load raw cognitive data from parquet."""
    raw_path = get_data_raw_path() / "cognitive_raw.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw cognitive data missing at {raw_path}")
    logger.info(f"Loading cognitive raw data from {raw_path}")
    return pd.read_parquet(raw_path)

def load_microbiome_raw_data():
    """Load raw microbiome data from parquet."""
    raw_path = get_data_raw_path() / "microbiome_raw.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw microbiome data missing at {raw_path}")
    logger.info(f"Loading microbiome raw data from {raw_path}")
    return pd.read_parquet(raw_path)

def apply_mice_imputation(df, target_col="z_score"):
    """
    Apply MICE imputation for missing values in the target column.
    Uses sklearn's IterativeImputer.
    """
    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer

    if df[target_col].isna().sum() == 0:
        logger.info("No missing values in target column, skipping imputation.")
        return df

    logger.info(f"Applying MICE imputation to {target_col}...")
    imputer = IterativeImputer(random_state=42, max_iter=10)
    
    # Prepare data for imputation (only numeric columns)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col not in numeric_cols:
        raise ValueError(f"Target column {target_col} is not numeric.")
    
    # Impute only the target column and other numeric predictors
    imputed_data = imputer.fit_transform(df[numeric_cols])
    df[numeric_cols] = imputed_data
    
    logger.info(f"MICE imputation complete. Remaining NaNs: {df[target_col].isna().sum()}")
    return df

def compute_z_scores(df, target_col="cognitive_score"):
    """Compute z-scores for the cognitive score column."""
    if target_col not in df.columns:
        raise KeyError(f"Column {target_col} not found in dataframe.")
    
    logger.info(f"Computing z-scores for {target_col}...")
    mean_val = df[target_col].mean()
    std_val = df[target_col].std()
    
    if std_val == 0:
        logger.warning("Standard deviation is zero. Setting z-scores to 0.")
        df["z_score"] = 0.0
    else:
        df["z_score"] = (df[target_col] - mean_val) / std_val
    
    return df

def filter_outliers_by_zscore(df, z_score_col="z_score", threshold=3.0):
    """
    Filter out outliers based on z-score > threshold.
    Returns the cleaned dataframe and a log of removed samples.
    """
    initial_count = len(df)
    if z_score_col not in df.columns:
        logger.warning(f"Z-score column '{z_score_col}' not found. Skipping outlier filtering.")
        return df, {"total_samples": initial_count, "removed_outliers": 0, "threshold": threshold}

    # Identify outliers
    outliers = df[abs(df[z_score_col]) > threshold]
    removed_count = len(outliers)
    cleaned_df = df[abs(df[z_score_col]) <= threshold].copy()

    log_entry = {
        "total_samples": initial_count,
        "removed_outliers": removed_count,
        "threshold": threshold
    }

    logger.info(f"Outlier filtering: Removed {removed_count} samples (threshold={threshold}).")
    return cleaned_df, log_entry

def save_processed_data(df, filename="merged_dataset.parquet"):
    """Save the processed dataframe to the processed directory."""
    output_path = get_data_processed_path() / filename
    ensure_dir(output_path)
    df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    return output_path

def ensure_dir(path):
    """Ensure a directory exists."""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")

def attempt_merge_and_report_gap(micro_df, cog_df):
    """
    Attempt to merge microbiome and cognitive data.
    If merge results in 0 rows, trigger fallback workflow.
    """
    logger.info("Attempting to merge microbiome and cognitive data...")
    
    # Attempt merge on participant_id / sample_id
    # Assuming standard column names based on schema: 'sample_id' vs 'participant_id'
    # We try to find common keys or use a standard join key if specified in contracts
    join_keys = [col for col in micro_df.columns if col in cog_df.columns]
    
    if not join_keys:
        # Fallback: try standard ID mapping if columns are named differently
        if 'sample_id' in micro_df.columns and 'participant_id' in cog_df.columns:
            join_keys = ['sample_id'] # Assuming sample_id in micro maps to participant_id in cog? 
            # Actually, usually they need to be renamed to match or we merge on a common ID.
            # Let's assume the ingestion step standardized them or we need to map.
            # For now, if no common keys, we can't merge.
            logger.error("No common columns found for merge.")
            return None, "No common columns found for merge."

    # Perform merge
    merged_df = pd.merge(micro_df, cog_df, on=join_keys, how="inner")
    
    if len(merged_df) == 0:
        logger.error("Merge resulted in 0 rows. Triggering fallback workflow.")
        return None, "No common participant IDs found."
    
    logger.info(f"Merge successful. Resulting rows: {len(merged_df)}")
    return merged_df, "Success"

def execute_fallback_workflow(reason):
    """
    Trigger the fallback workflow (T017b, T017d) if merge fails.
    This function calls the gap report script.
    """
    logger.warning(f"Executing fallback workflow due to: {reason}")
    # Import here to avoid circular imports if utils calls this
    import subprocess
    # Run the gap report script
    subprocess.run([sys.executable, str(Path(__file__).parent / "07_gap_report.py")], check=True)
    sys.exit(0)

def write_filtering_log(log_entry):
    """
    Write the filtering log to data/qc/filtering_log.json.
    Schema: { "total_samples": int, "removed_outliers": int, "threshold": float }
    """
    qc_path = get_data_qc_path()
    ensure_dir(qc_path)
    log_file = qc_path / "filtering_log.json"
    write_json_log(log_entry, log_file)
    logger.info(f"Filtering log written to {log_file}")

def main():
    """Main execution flow for preprocessing."""
    try:
        # 1. Load Raw Data
        cog_raw = load_cognitive_raw_data()
        micro_raw = load_microbiome_raw_data()

        # 2. Preprocess Cognitive Data
        # Impute missing values
        cog_clean = apply_mice_imputation(cog_raw, target_col="cognitive_score")
        # Compute z-scores
        cog_clean = compute_z_scores(cog_clean, target_col="cognitive_score")

        # 3. Merge Data
        merged_df, status = attempt_merge_and_report_gap(micro_raw, cog_clean)

        if merged_df is None:
            execute_fallback_workflow(status)
            return

        # 4. Outlier Filtering (T015)
        # Apply z-score > 3 filter on the merged dataset
        cleaned_df, filter_log = filter_outliers_by_zscore(
            merged_df, 
            z_score_col="z_score", 
            threshold=3.0
        )

        # 5. Write Filtering Log (T015 Requirement)
        write_filtering_log(filter_log)

        # 6. Save Processed Data
        save_processed_data(cleaned_df, "merged_dataset.parquet")

        logger.info("Preprocessing complete.")

    except FileNotFoundError as e:
        logger.error(f"Raw data files missing. Cannot perform preprocessing.")
        # If raw data is missing, we cannot proceed. 
        # Depending on spec, this might trigger a gap report or just fail.
        # Given T014 logic, if we can't even load, we treat as gap.
        execute_fallback_workflow("Raw data files missing.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error during preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
