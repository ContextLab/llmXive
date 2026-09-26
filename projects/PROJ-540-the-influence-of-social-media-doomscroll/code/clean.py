"""
Data cleaning module for the Doomscrolling Anxiety Analysis Pipeline.
Implements listwise deletion and power checks per Spec FR-002.
"""
import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from config import load_config, ensure_directories
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load raw data for cleaning."""
    logger.info(f"Loading data from: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def validate_cleaned_data(df: pd.DataFrame) -> bool:
    """Validate that cleaned data meets requirements."""
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    if len(df) == 0:
        logger.error("DataFrame is empty after cleaning.")
        return False
    
    return True

def apply_listwise_deletion(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Apply listwise deletion for missing predictor/outcome values.
    Enforces N < 30 hard stop per Spec FR-002.
    
    - If N < 30: Raise PowerLimitationError
    - If 30 <= N < 100: Log warning and proceed
    - If N >= 100: Proceed normally
    """
    logger.info("Applying listwise deletion...")
    
    # Drop rows with missing values in required columns
    initial_n = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    final_n = len(df_clean)
    dropped_count = initial_n - final_n
    
    logger.info(f"Rows before deletion: {initial_n}")
    logger.info(f"Rows after deletion: {final_n}")
    logger.info(f"Rows dropped: {dropped_count}")
    
    # Log missing value statistics
    missing_stats = df[REQUIRED_COLUMNS].isnull().sum()
    logger.info(f"Missing value statistics:\n{missing_stats}")
    
    # Power check per Spec FR-002
    if final_n < 30:
        error_msg = f"Power limitation: N = {final_n} < 30. Analysis cannot proceed."
        logger.error(error_msg)
        logger.error("Spec baseline N < 30 active")
        raise PowerLimitationError(error_msg)
    elif final_n < 100:
        logger.warning(f"Low Power (30 <= N < 100): N = {final_n}")
    
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: Optional[Path] = None):
    """Save cleaned data to disk."""
    if output_path is None:
        output_path = Path("data/processed/analysis_data.csv")
    
    ensure_directories()
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to: {output_path}")
    logger.info(f"Final N: {len(df)}")

def main():
    """CLI entry point for cleaning."""
    try:
        input_path = Path("data/raw/parsed_data.csv")
        if not input_path.exists():
            # Try alternative path
            input_path = Path("data/processed/analysis_data.csv")
            if not input_path.exists():
                logger.error("No input data found for cleaning.")
                return 1
        
        df = load_cleaned_data(input_path)
        df_clean = apply_listwise_deletion(df)
        
        if df_clean is not None:
            save_cleaned_data(df_clean)
            return 0
        return 1
    except PowerLimitationError as e:
        logger.error(f"Power limitation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during cleaning: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
