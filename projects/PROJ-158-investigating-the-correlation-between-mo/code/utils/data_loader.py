"""
Data loading utilities.
"""
import pandas as pd
from pathlib import Path
from typing import Union
from utils.logger import setup_logger

logger = setup_logger("data_loader")

def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads a CSV file into a pandas DataFrame.
    """
    path = Path(path)
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    logger.info(f"Loading CSV from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def save_csv(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """
    Saves a pandas DataFrame to a CSV file.
    """
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    
    logger.info(f"Saving CSV to {path}")
    df.to_csv(path, index=False)
    logger.info("Saved successfully")
