"""
T017 Implementation: Output cleaned and standardized data.

This module implements the final step of the US1 data pipeline:
1. Loads the preprocessed data from code/preprocessing/preprocess.py output.
2. Validates the presence of required columns.
3. Standardizes numeric columns to a 0-1 range (min-max scaling) where appropriate.
4. Documents the scoring method in a metadata file.
5. Writes the final `data/processed/cleaned_data.csv`.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import from sibling modules as per API surface
# The API surface indicates code/preprocessing/preprocess.py exists and exports run_preprocessing
# However, since T014/T015 were marked as failed/missing in the feedback, we must ensure
# we can load the *intermediate* data. The pipeline structure suggests:
# download -> generate -> preprocess -> output_cleaned
# We assume preprocess.py writes a temporary intermediate file or we read the raw source
# if preprocess is not yet fully functional in the runner environment.
# To be robust, we will look for the intermediate file produced by the hypothetical
# successful run of T014, or fall back to reading the synthetic data directly if T014
# hasn't written the intermediate yet, but strictly following the "no synthetic fallback"
# rule for *input* data, we assume the intermediate file exists from T014.

# Based on the project structure, T014 (preprocess) should have produced a file.
# We will assume the standard output path for the preprocessing step is:
# data/processed/intermediate_features.csv (or similar).
# If that file doesn't exist, we must fail loudly as per constraints.

INTERMEDIATE_DATA_PATH = Path("data/processed/intermediate_features.csv")
OUTPUT_DATA_PATH = Path("data/processed/cleaned_data.csv")
METADATA_PATH = Path("data/processed/cleaning_metadata.json")

# Required columns as per T004 schema and task description
REQUIRED_COLUMNS = [
    "participant_id",
    "latency",
    "smoothness",
    "lead_time",
    "agency_score"
]

# Columns to standardize (0-1 range)
STANDARDIZE_COLUMNS = ["latency", "smoothness", "lead_time", "agency_score"]

def standardize_column(series: pd.Series, method: str = "minmax") -> pd.Series:
    """
    Standardizes a pandas Series to a 0-1 range using min-max scaling.
    
    Args:
        series: The input pandas Series.
        method: Scaling method (currently only 'minmax' supported).
        
    Returns:
        A new Series with values scaled to [0, 1].
    """
    if series.dtype not in [np.float64, np.float32, np.int64, np.int32]:
        return series
        
    min_val = series.min()
    max_val = series.max()
    
    if max_val == min_val:
        # Avoid division by zero; if all values are same, return 0.5 or the value
        return pd.Series([0.5] * len(series), index=series.index)
        
    return (series - min_val) / (max_val - min_val)

def run_cleaning_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None
) -> bool:
    """
    Executes the cleaning and standardization pipeline.
    
    1. Loads intermediate data.
    2. Validates schema.
    3. Standardizes numeric features.
    4. Writes cleaned CSV and metadata.
    
    Returns:
        True if successful, False otherwise.
    """
    input_path = input_path or INTERMEDIATE_DATA_PATH
    output_path = output_path or OUTPUT_DATA_PATH
    metadata_path = metadata_path or METADATA_PATH
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    if not input_path.exists():
        raise FileNotFoundError(
            f"Intermediate data file not found at {input_path}. "
            "Ensure T014 (preprocess.py) has run successfully and written the intermediate file."
        )
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read intermediate data: {e}")
    
    # 2. Validate Schema
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Intermediate data missing required columns: {missing_cols}. "
            f"Expected: {REQUIRED_COLUMNS}"
        )
    
    # 3. Standardize Columns
    # We standardize the numeric features to [0, 1] as requested for T017
    df_standardized = df.copy()
    standardization_info = {}
    
    for col in STANDARDIZE_COLUMNS:
        if col in df_standardized.columns:
            original_min = df_standardized[col].min()
            original_max = df_standardized[col].max()
            df_standardized[col] = standardize_column(df_standardized[col])
            standardization_info[col] = {
                "original_min": float(original_min),
                "original_max": float(original_max),
                "scaled_min": float(df_standardized[col].min()),
                "scaled_max": float(df_standardized[col].max())
            }
    
    # 4. Document Scoring Method
    metadata = {
        "task_id": "T017",
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
        "scoring_method": "Min-Max Normalization to [0, 1] range",
        "standardization_details": standardization_info,
        "row_count": len(df_standardized),
        "columns": list(df_standardized.columns),
        "notes": "Data derived from synthetic generator (T013) as per project scope (T000). "
                 "No human participants involved. Real data path disabled."
    }
    
    # 5. Write Output
    df_standardized.to_csv(output_path, index=False)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Successfully wrote cleaned data to {output_path} ({len(df_standardized)} rows)")
    print(f"Metadata written to {metadata_path}")
    
    return True

def main():
    """Entry point for T017 execution."""
    try:
        success = run_cleaning_pipeline()
        if success:
            print("T017: Output generation completed successfully.")
            return 0
        else:
            print("T017: Output generation failed.")
            return 1
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        return 1
    except ValueError as e:
        print(f"VALIDATION ERROR: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
