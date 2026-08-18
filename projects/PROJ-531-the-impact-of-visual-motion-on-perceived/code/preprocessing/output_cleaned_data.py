import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from utils.logging_config import get_logger
from utils.config import get_config

logger = get_logger(__name__)

def standardize_column(series: pd.Series, method: str = "minmax") -> pd.Series:
    """
    Standardize a numeric column to a 0-1 range (min-max scaling).
    
    Args:
        series: The pandas Series to standardize.
        method: Currently only 'minmax' is supported.
    
    Returns:
        A standardized Series in the range [0, 1].
    """
    if method != "minmax":
        raise ValueError(f"Unsupported standardization method: {method}")
    
    if series.min() == series.max():
        # Avoid division by zero; return 0.5 (neutral) or 0 depending on preference
        return pd.Series(np.full_like(series, 0.5, dtype=float))
    
    return (series - series.min()) / (series.max() - series.min())

def run_cleaning_pipeline(input_path: str, output_path: str) -> dict:
    """
    Loads raw/preprocessed data, standardizes key metrics, and saves the cleaned dataset.
    
    This implements T017: Output `data/processed/cleaned_data.csv` with documented 
    scoring method and standardization (0–1 range).
    
    Args:
        input_path: Path to the preprocessed data (e.g., from T014/T015).
        output_path: Path where the cleaned CSV will be written.
    
    Returns:
        A dictionary containing metadata about the cleaning process.
    """
    logger.info(f"Starting cleaning pipeline. Input: {input_path}, Output: {output_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Identify columns to standardize based on project requirements (FR-002, FR-003)
    # Typically: latency, smoothness, lead_time, agency_score
    # We standardize the target (agency_score) and key predictors to 0-1 range
    columns_to_standardize = []
    
    # Heuristic: Standardize numeric columns that are likely scores or normalized metrics
    # excluding participant_id or other identifiers
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ['participant_id', 'id', 'run_id']
    columns_to_standardize = [c for c in numeric_cols if c not in exclude_cols]
    
    logger.info(f"Standardizing columns: {columns_to_standardize}")
    
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "output_file": output_path,
        "standardization_method": "minmax",
        "standardized_columns": columns_to_standardize,
        "n_rows_before": len(df),
        "n_rows_after": len(df),
        "scoring_method_documentation": (
            "All numeric metrics (latency, smoothness, lead_time, agency_score) "
            "are standardized to [0, 1] using min-max scaling. "
            "This ensures comparability across features with different units and scales."
        )
    }
    
    for col in columns_to_standardize:
        df[col] = standardize_column(df[col])
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    logger.info(f"Cleaned data saved to {output_path} with {len(df)} rows.")
    
    return metadata

def main():
    """Entry point for T017: Output cleaned data."""
    config = get_config()
    
    # Default paths based on project structure
    input_path = config.get("paths.preprocessed_data", "data/processed/preprocessed_data.csv")
    output_path = config.get("paths.cleaned_data", "data/processed/cleaned_data.csv")
    
    # Allow override via environment variables
    if os.getenv("INPUT_DATA_PATH"):
        input_path = os.getenv("INPUT_DATA_PATH")
    if os.getenv("OUTPUT_DATA_PATH"):
        output_path = os.getenv("OUTPUT_DATA_PATH")
    
    try:
        metadata = run_cleaning_pipeline(input_path, output_path)
        
        # Save metadata as JSON for provenance
        metadata_path = str(Path(output_path).with_suffix('.json'))
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Successfully cleaned data. Output: {output_path}")
        print(f"Metadata saved to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Failed to clean data: {e}")
        raise

if __name__ == "__main__":
    main()
