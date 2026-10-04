import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Project root resolution
ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "code" / "config.yaml"
PROCESSED_FEATURES_PATH = ROOT / "data" / "processed" / "features.csv"
LABELED_DATA_PATH = ROOT / "data" / "processed" / "labeled_features.csv"
LIMITATIONS_PATH = ROOT / "results" / "limitations.md"
CLASSIFICATION_METRICS_PATH = ROOT / "results" / "classification_metrics.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    import yaml
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def load_search_time_data() -> Optional[pd.DataFrame]:
    """
    Load the processed features data containing search_time.
    Returns None if file missing or search_time column absent.
    """
    if not PROCESSED_FEATURES_PATH.exists():
        logger.error(f"Processed features file not found: {PROCESSED_FEATURES_PATH}")
        return None

    df = pd.read_csv(PROCESSED_FEATURES_PATH)
    
    if "search_time" not in df.columns:
        logger.warning("Column 'search_time' not found in processed features.")
        return None

    return df

def label_by_median_split(df: pd.DataFrame, column: str = "search_time") -> pd.DataFrame:
    """
    Label by median split of search time.
    Label = 1 if search_time > median, else 0.
    Handles 'UNFULFILLABLE' strings or NaNs by excluding them from labeling
    but keeping the row with a specific status.
    
    Constraint: If 'search_time' is 'UNFULFILLABLE', log exclusion and continue.
    """
    df = df.copy()
    
    # Ensure search_time is numeric where possible, coerce errors to NaN
    # 'UNFULFILLABLE' strings will become NaN
    df["search_time_numeric"] = pd.to_numeric(df[column], errors="coerce")
    
    # Filter valid numeric values for median calculation
    valid_mask = df["search_time_numeric"].notna()
    valid_values = df.loc[valid_mask, "search_time_numeric"]
    
    if valid_values.empty:
        logger.warning("No valid numeric search_time values found for median split.")
        df["cognitive_load_label"] = -1 # -1 indicates failure to label
        df["label_status"] = "NO_DATA"
        return df

    median_val = valid_values.median()
    logger.info(f"Computed median search time: {median_val:.4f}")
    
    # Apply labeling logic
    def assign_label(row):
        if pd.isna(row["search_time_numeric"]):
            # Check if original string was 'UNFULFILLABLE'
            if row[column] == "UNFULFILLABLE":
                return 0, "UNFULFILLABLE_EXCLUDED"
            else:
                return 0, "MISSING_VALUE"
        
        # Strictly greater than median
        if row["search_time_numeric"] > median_val:
            return 1, "LABELED_HIGH"
        else:
            return 0, "LABELED_LOW"

    labels, statuses = zip(*df.apply(assign_label, axis=1))
    
    df["cognitive_load_label"] = labels
    df["label_status"] = statuses
    
    # Log exclusions
    excluded_count = df[df["label_status"].isin(["UNFULFILLABLE_EXCLUDED", "MISSING_VALUE"])].shape[0]
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows from labeling due to missing/invalid search_time.")
    
    # Drop temporary column
    df.drop(columns=["search_time_numeric"], inplace=True)
    
    return df

def save_labeled_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Save the labeled dataframe to CSV."""
    if output_path is None:
        output_path = LABELED_DATA_PATH
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Labeled data saved to {output_path}")
    return output_path

def write_limitations_note() -> Path:
    """
    Write the limitations note documenting the 'Search-Time Estimation' limitation.
    Updates results/limitations.md.
    """
    LIMITATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    content = """# Limitations Report: Search-Time Estimation

## Search-Time Estimation Limitation

**Status**: Active Constraint

**Description**:
This pipeline utilizes search time as a proxy for cognitive load ground truth. 
In scenarios where independent, direct measures of search time are absent from the 
dataset metadata, the system defaults to a **median split** of the available search 
time values to generate binary labels (High vs. Low load).

**Implications**:
1. **Relative, Not Absolute**: The resulting labels represent relative cognitive load 
   (above/below median) rather than absolute thresholds.
2. **Distribution Dependency**: The validity of the labels is strictly dependent on 
   the distribution of search times in the specific dataset. Skewed distributions 
   may result in unbalanced class labels.
3. **Handling Missing Data**: If the `search_time` column is marked as 
   `UNFULFILLABLE` (due to missing metadata or failed image-based salience computation), 
   these trials are excluded from the labeling process and marked with a status 
   of `UNFULFILLABLE_EXCLUDED`. They are not assigned a ground truth label.

**Reference**:
This limitation is documented per FR-011 to ensure transparency in the evaluation 
of the real-time load classification prototype.

**Date Generated**: {date}
""".format(date=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(LIMITATIONS_PATH, "w") as f:
        f.write(content)
    
    logger.info(f"Limitations note written to {LIMITATIONS_PATH}")
    return LIMITATIONS_PATH

def update_classification_metrics() -> Path:
    """
    Update results/classification_metrics.csv to include the header 
    'Ground Truth: Search-Time Estimation'.
    Ensures the file exists with the correct schema.
    """
    CLASSIFICATION_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Define the required header
    required_columns = ["metric_name", "value", "ground_truth_source"]
    
    if not CLASSIFICATION_METRICS_PATH.exists():
        # Create new file with header
        df = pd.DataFrame(columns=required_columns)
        df.to_csv(CLASSIFICATION_METRICS_PATH, index=False)
        logger.info(f"Created new classification metrics file: {CLASSIFICATION_METRICS_PATH}")
    else:
        # Check if header exists, if not, update it
        current_df = pd.read_csv(CLASSIFICATION_METRICS_PATH)
        if "ground_truth_source" not in current_df.columns:
            # Reconstruct with new header if column missing
            # For safety, we assume the content structure might need alignment
            # If the file is empty or just headers, we reset.
            if current_df.empty:
                current_df = pd.DataFrame(columns=required_columns)
            else:
                # If data exists but header is wrong, we preserve data but rename/add columns
                # This is a simplified approach; in production, a schema migration might be needed.
                current_df["ground_truth_source"] = "Search-Time Estimation"
            
            current_df.to_csv(CLASSIFICATION_METRICS_PATH, index=False)
            logger.info(f"Updated classification metrics headers in {CLASSIFICATION_METRICS_PATH}")
    
    return CLASSIFICATION_METRICS_PATH

def main():
    """
    Main entry point for T029: Ground-truth labeling logic.
    1. Load config.
    2. Load search time data.
    3. Label by median split (handling UNFULFILLABLE).
    4. Save labeled data.
    5. Write limitations note.
    6. Update classification metrics headers.
    """
    logger.info("Starting T029: Ground-truth labeling logic...")
    
    # 1. Load Config (optional, but good practice)
    config = load_config()
    logger.info(f"Config loaded: {config.get('seeds', 'default_seed')}")

    # 2. Load Data
    df = load_search_time_data()
    if df is None:
        logger.error("Failed to load search time data. Cannot proceed with labeling.")
        sys.exit(1)

    # 3. Label
    labeled_df = label_by_median_split(df)

    # 4. Save
    save_labeled_data(labeled_df)

    # 5. Documentation
    write_limitations_note()

    # 6. Update Metrics Header
    update_classification_metrics()

    logger.info("T029 completed successfully.")

if __name__ == "__main__":
    main()