import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_processed_data_dir, get_logs_dir, ensure_directories, set_global_seed
from code.src.utils.validation import load_schema, validate_dataframe_against_schema

# Configure logging
LOGS_DIR = get_logs_dir()
ensure_directories()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'filtering.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Required covariates as per spec FR-002 and dataset.schema.yaml
REQUIRED_COVARIATES = ['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use']
REQUIRED_METRICS = ['shannon_diversity', 'cognitive_flexibility_score']

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a column has zero variance (all values are the same).
    Returns True if zero variance is detected, False otherwise.
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in dataframe.")
        return True  # Treat missing as zero variance for safety

    unique_values = df[column].nunique()
    if unique_values <= 1:
        logger.warning(f"Column '{column}' has zero variance (unique values: {unique_values}).")
        return True
    return False

def filter_cohort(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Filter the cohort based on:
    1. Age >= 65
    2. Non-null Shannon Diversity and Cognitive Flexibility Score
    3. Non-null Required Covariates (listwise deletion)
    4. Zero-variance check (flag and skip if detected in critical columns)

    Args:
        input_path: Path to the ingested dataset (CSV).
        output_path: Path to save the filtered cohort (CSV).

    Returns:
        Filtered pandas DataFrame.
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    # 1. Filter for Age >= 65
    logger.info("Filtering for age >= 65...")
    initial_count = len(df)
    df = df[df['age'] >= 65]
    dropped_age = initial_count - len(df)
    logger.info(f"Dropped {dropped_age} rows due to age < 65. Remaining: {len(df)}")

    # 2. Check Zero Variance in Critical Columns before dropping nulls
    # We check the metrics and covariates that will be used in analysis
    critical_cols = REQUIRED_METRICS + REQUIRED_COVARIATES
    for col in critical_cols:
        if col in df.columns:
            if check_zero_variance(df, col):
                logger.error(f"Critical column '{col}' has zero variance. Analysis cannot proceed safely.")
                # Depending on strictness, we might raise an error here.
                # For this task, we flag it but continue to see if data exists.

    # 3. Listwise Deletion for Missing Values
    # Drop rows where any of the required metrics or covariates are null
    logger.info("Applying listwise deletion for missing required fields...")
    cols_to_check = REQUIRED_METRICS + REQUIRED_COVARIATES
    missing_cols = [c for c in cols_to_check if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns in dataset: {missing_cols}. Skipping deletion for these.")
    else:
        initial_count = len(df)
        df = df.dropna(subset=cols_to_check)
        dropped_nulls = initial_count - len(df)
        logger.info(f"Dropped {dropped_nulls} rows due to missing required data. Remaining: {len(df)}")

    # 4. Final Zero Variance Check on the filtered set
    # If the remaining dataset has zero variance in the target variable, log a warning
    if len(df) > 0:
        for col in REQUIRED_METRICS:
            if check_zero_variance(df, col):
                logger.warning(f"Final dataset has zero variance in '{col}'.")

    # 5. Validate against schema (optional but good practice before saving)
    schema_path = Path("code/contracts/dataset.schema.yaml")
    if schema_path.exists():
        try:
            schema = load_schema(schema_path)
            validate_dataframe_against_schema(df, schema)
            logger.info("Filtered cohort validated against schema.")
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            # We proceed to save, but log the error

    # Ensure output directory exists
    ensure_directories()
    
    logger.info(f"Saving filtered cohort to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")

    return df

def main():
    """Main entry point for the filtering script."""
    set_global_seed()
    processed_dir = get_processed_data_dir()
    
    input_file = processed_dir.parent / "raw" / "synthetic_data.csv" # Assuming ingestion output location
    # If ingestion saved directly to processed, adjust path. 
    # Based on T010, ingestion saves to data/processed/merged_cohort.csv or similar.
    # Let's assume the standard path from T010 logic:
    input_file = Path("code/data/raw/synthetic_data.csv") 
    
    # Correction: T010 says "Ingest ... from data/raw". 
    # T011 says "Save output to data/processed/filtered_cohort.csv".
    # We need to know where T010 saved the data. 
    # Assuming T010 saved to data/raw/synthetic_data.csv (as per T008) or a merged file.
    # The task description for T010 says "Load ... from data/raw/synthetic_data.csv".
    # It doesn't explicitly state where it saves. Let's assume it saves to data/processed/merged_cohort.csv.
    # However, the T011 description says "filter ... from data/raw (synthetic)".
    # Let's assume the input is the synthetic data generated in T008 which is at data/raw/synthetic_data.csv.
    # Wait, T010 says "Ingest ... from data/raw". It likely produces a merged file.
    # Let's check T008: "Output to data/raw/synthetic_data.csv".
    # If T010 merges, it might output to data/processed/merged_cohort.csv.
    # To be safe, we will look for the most likely input from T010.
    # If T010 didn't save a merged file, we use the raw synthetic data.
    
    # Standardizing paths based on project structure:
    raw_data_path = Path("code/data/raw/synthetic_data.csv")
    processed_data_path = Path("code/data/processed/filtered_cohort.csv")
    
    # If the ingestion script (T010) produced a merged file, we should use that.
    # But since T010 is "Implement ingestion", and T011 is "Implement filtering",
    # we assume the input for T011 is the output of T010.
    # If T010 saved to data/processed/merged_cohort.csv, we use that.
    # If not, we fallback to raw.
    
    input_candidates = [
        Path("code/data/processed/merged_cohort.csv"),
        Path("code/data/raw/synthetic_data.csv")
    ]
    
    input_file = None
    for candidate in input_candidates:
        if candidate.exists():
            input_file = candidate
            logger.info(f"Found input file: {input_file}")
            break
    
    if input_file is None:
        logger.error("No input file found. Expected merged_cohort.csv or synthetic_data.csv.")
        sys.exit(1)

    output_file = Path("code/data/processed/filtered_cohort.csv")
    
    try:
        filtered_df = filter_cohort(input_file, output_file)
        logger.info("Filtering completed successfully.")
    except Exception as e:
        logger.error(f"Filtering failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()