import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from src.config import load_config

logger = logging.getLogger(__name__)

def save_correlation_results(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    force: bool = False
) -> Path:
    """
    Save correlation results to a CSV file.
    
    Args:
        df: DataFrame containing correlation results with columns:
            r, p, q, is_moderate, is_meaningful, status
        output_path: Optional custom output path. If None, uses config default.
        force: If True, overwrite existing file.
    
    Returns:
        Path to the saved file.
    
    Raises:
        FileNotFoundError: If input DataFrame is empty and status is not 'blocked'.
        FileExistsError: If file exists and force=False.
        ValueError: If required columns are missing.
    """
    config = load_config()
    
    # Determine output path
    if output_path is None:
        output_path = str(Path(config['DATA_PROCESSED']) / 'correlation_results.csv')
    
    output_file = Path(output_path)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate required columns
    required_columns = ['r', 'p', 'q', 'is_moderate', 'is_meaningful', 'status']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for blocked status or valid data
    is_blocked = df.get('status', ['unknown'] * len(df)).iloc[0] == 'blocked' if len(df) > 0 else False
    
    if len(df) == 0 and not is_blocked:
        raise FileNotFoundError("Input DataFrame is empty and status is not 'blocked'. "
                              "This suggests upstream tasks failed to generate data.")
    
    # Check if file exists
    if output_file.exists() and not force:
        raise FileExistsError(f"Output file already exists: {output_file}. Set force=True to overwrite.")
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Saved correlation results to {output_file} with {len(df)} rows")
    
    return output_file
