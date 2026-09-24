import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.validation import setup_logger

DESCRIPTORS_PATH = Path("data/descriptors.csv")
STRATIFIED_OUTPUT_PATH = Path("data/cleaned/stratified_data.csv")

def classify_chemistry(composition: str) -> str:
    """
    Classify the chemistry class based on composition string.
    Returns 'oxide', 'halide', 'nitride', or 'unknown'.
    """
    if not isinstance(composition, str):
        return 'unknown'
    comp_lower = composition.lower()
    if 'o' in comp_lower and 'ox' in comp_lower: # Simple heuristic
        return 'oxide'
    if 'f' in comp_lower or 'cl' in comp_lower or 'br' in comp_lower or 'i' in comp_lower:
        return 'halide'
    if 'n' in comp_lower and 'nit' in comp_lower:
        return 'nitride'
    return 'unknown'

def stratify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'chemistry_class' column to the dataframe.
    """
    if 'composition' in df.columns:
        df['chemistry_class'] = df['composition'].apply(classify_chemistry)
    elif 'chemistry_class' in df.columns:
        pass # Already classified
    else:
        # Fallback: assume all are 'oxide' if no composition info
        df['chemistry_class'] = 'oxide'
    return df

def save_stratified_data(df: pd.DataFrame, output_path: Path):
    """
    Save the stratified dataframe.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

def main():
    """
    Main entry point for stratification.
    """
    logger = setup_logger("stratify")
    
    if not DESCRIPTORS_PATH.exists():
        logger.error(f"Input file {DESCRIPTORS_PATH} not found.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(DESCRIPTORS_PATH)
    except Exception as e:
        logger.error(f"Failed to read {DESCRIPTORS_PATH}: {e}")
        sys.exit(1)
    
    df = stratify_dataframe(df)
    save_stratified_data(df, STRATIFIED_OUTPUT_PATH)
    logger.info(f"Stratified data saved to {STRATIFIED_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
