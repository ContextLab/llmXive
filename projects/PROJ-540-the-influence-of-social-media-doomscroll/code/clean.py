import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from config import load_config, ensure_directories, set_seed
from exceptions import PowerLimitationError
from validity import check_construct_validity

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load the raw dataset from the specified path."""
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def validate_cleaned_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the schema and check for missing values in required columns."""
    logger.info("Validating schema and missing values...")
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check construct validity (baseline_anxiety vs anxiety_score)
    check_construct_validity(df)
    
    # Count missing values before deletion
    initial_rows = len(df)
    missing_counts = df[REQUIRED_COLUMNS].isnull().sum()
    logger.info(f"Missing value counts before deletion:\n{missing_counts}")
    
    # Listwise deletion for predictor/outcome
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped_rows = initial_rows - len(df_clean)
    
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows due to missing values.")
    
    # Power check
    if len(df_clean) < 30:
        logger.error(f"Sample size {len(df_clean)} is below the hard limit of 30.")
        raise PowerLimitationError(f"Insufficient sample size: {len(df_clean)} < 30. Analysis cannot proceed.")
    
    if len(df_clean) < 100:
        logger.warning(f"Low power warning: Sample size is {len(df_clean)} (< 100). Results may be underpowered.")
    
    logger.info(f"Validation complete. Final sample size: {len(df_clean)}")
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the cleaned dataframe to the specified path."""
    logger.info(f"Saving cleaned data to {output_path}")
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")

def main() -> None:
    """Main entry point for the cleaning pipeline."""
    config = load_config()
    seed = config.get('random_seed')
    set_seed(seed)
    
    input_path = Path(config['paths']['raw_data'])
    output_path = Path(config['paths']['processed_data'])
    
    try:
        df_raw = load_cleaned_data(input_path)
        df_clean = validate_cleaned_data(df_raw)
        save_cleaned_data(df_clean, output_path)
        logger.info("Data cleaning pipeline completed successfully.")
    except PowerLimitationError as e:
        logger.critical(f"Pipeline halted due to power limitation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
