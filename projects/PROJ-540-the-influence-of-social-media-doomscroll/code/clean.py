import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "news_exposure_freq",
    "anxiety_score",
    "baseline_anxiety",
    "age",
    "gender"
]

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"CLEAN: {message}")

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load data from a CSV file."""
    _log_step(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def validate_cleaned_data(df: pd.DataFrame) -> None:
    """Validate that the dataframe contains required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def apply_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply listwise deletion for missing predictor/outcome values.
    Enforces N < 130 hard stop per ratified amendment T036.
    """
    _log_step("Applying listwise deletion")
    
    # Log Spec baseline vs Plan override
    logger.info("INFO: Spec baseline N < 30 (Legacy) - Plan override N < 130 active")
    
    initial_n = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    final_n = len(df_clean)
    dropped = initial_n - final_n
    
    _log_step(f"Rows before: {initial_n}, Rows after: {final_n}, Dropped: {dropped}")
    
    # Power check logic
    if final_n < 130:
        logger.error(f"ERROR: Power limitation. N < 130 (N={final_n})")
        raise PowerLimitationError(f"N < 130: {final_n}")
    
    if 130 <= final_n < 200:
        logger.warning(f"WARNING: Low Power (130 <= N < 200). Current N: {final_n}")
    
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save cleaned dataframe to CSV."""
    _log_step(f"Saving cleaned data to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

def main() -> None:
    """Main entry point for cleaning script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    input_path = Path("data/raw/parsed_data.csv")
    output_path = Path("data/processed/analysis_data.csv")
    
    try:
        df = load_cleaned_data(input_path)
        validate_cleaned_data(df)
        df_clean = apply_listwise_deletion(df)
        save_cleaned_data(df_clean, output_path)
        logger.info(f"Cleaning complete. Final N: {len(df_clean)}")
    except PowerLimitationError as e:
        logger.error(f"Power limitation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during cleaning: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
