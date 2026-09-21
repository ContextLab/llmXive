"""
Stratification module for perovskite chemistry classes.

This module implements FR-014: Stratification by perovskite chemistry class
(oxide, halide, nitride) for correlation analysis.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import seed manager for deterministic operations if needed
try:
    from src.utils.seed_manager import get_seed
except ImportError:
    # Fallback if running from root or different structure
    import random
    def get_seed():
        return 42


def setup_logger_module(name: str = "stratify") -> logging.Logger:
    """
    Setup a logger for the stratify module.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def classify_chemistry(formula: str) -> str:
    """
    Classify a perovskite formula into its chemistry class.

    Args:
        formula: Chemical formula string (e.g., "BaTiO3", "CsPbI3").

    Returns:
        Chemistry class: 'oxide', 'halide', 'nitride', or 'unknown'.
    """
    if not isinstance(formula, str):
        return "unknown"

    formula = formula.strip().lower()

    # Check for oxides (O in formula)
    # Note: We assume the formula is normalized (e.g., O3, not O_3)
    # Standard perovskite ABX3 where X is the anion
    if 'o' in formula and 'n' not in formula and 'f' not in formula and 'cl' not in formula and 'br' not in formula and 'i' not in formula:
        # Simple heuristic: if 'o' is present and no other common halogens/nitrides
        # This is a heuristic; real chemistry might be more complex
        # We check specifically for 'o' not being part of 'no' (nitrogen oxide) or similar
        # A more robust way is to check the anion position, but for string matching:
        # Oxides usually end in O3 or contain O without other halogens
        # Let's refine: check for 'o' and absence of halogens
        has_halogen = any(h in formula for h in ['f', 'cl', 'br', 'i'])
        has_nitride = 'n' in formula and 'no' not in formula # 'no' could be nitric oxide, but in perovskites N usually means Nitride if X=N
        # Actually, Nitrides are X=N. Halides are X=F, Cl, Br, I. Oxides are X=O.
        # Formula strings like "BaTiO3" -> O is present. "CsPbI3" -> I is present.
        # "GaN" is not perovskite usually, but "LaFeO3" is.
        # Let's use the explicit presence of the anion character.
        
        if not has_halogen:
            # Check if it's likely an oxide (O present)
            if 'o' in formula:
                return 'oxide'
    
    # Check for halides (F, Cl, Br, I)
    if any(h in formula for h in ['f', 'cl', 'br', 'i']):
        return 'halide'
    
    # Check for nitrides (N, but not part of 'no' or other groups if possible)
    # In perovskites, Nitride is usually X=N.
    # If 'n' is present and no 'o', 'f', 'cl', 'br', 'i'
    if 'n' in formula and not any(x in formula for x in ['o', 'f', 'cl', 'br', 'i']):
        return 'nitride'

    return 'unknown'


def stratify_dataframe(df: pd.DataFrame, formula_column: str = 'formula') -> pd.DataFrame:
    """
    Add a 'chemistry_class' column to the dataframe based on the formula.

    Args:
        df: Input DataFrame containing perovskite data.
        formula_column: Name of the column containing chemical formulas.

    Returns:
        DataFrame with an added 'chemistry_class' column.
    
    Raises:
        ValueError: If the formula column is missing.
    """
    logger = setup_logger_module()
    
    if formula_column not in df.columns:
        # Try to find a similar column if exact match fails
        possible_cols = [c for c in df.columns if 'formula' in c.lower() or 'composition' in c.lower()]
        if possible_cols:
            formula_column = possible_cols[0]
            logger.warning(f"Column '{formula_column}' not found, using '{formula_column}' instead.")
        else:
            raise ValueError(f"Column '{formula_column}' not found in dataframe. Available columns: {list(df.columns)}")

    logger.info(f"Stratifying dataframe by '{formula_column}' into chemistry classes.")
    
    df = df.copy()
    df['chemistry_class'] = df[formula_column].apply(classify_chemistry)
    
    class_counts = df['chemistry_class'].value_counts()
    logger.info(f"Stratification complete. Class counts:\n{class_counts}")
    
    # Log warning if 'unknown' class is significant
    if 'unknown' in class_counts.index and class_counts['unknown'] > 0:
        logger.warning(f"Found {class_counts['unknown']} entries classified as 'unknown'.")
        
    return df


def save_stratified_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the stratified dataframe to a CSV file.

    Args:
        df: The stratified DataFrame.
        output_path: Path to save the CSV file.
    """
    logger = setup_logger_module()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Stratified data saved to {output_path}")


def main():
    """
    Main entry point for the stratify script.
    
    Usage:
        python -m src.analysis.stratify --input <path> --output <path>
    """
    logger = setup_logger_module()
    
    parser = argparse.ArgumentParser(description="Stratify perovskite data by chemistry class.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file.")
    parser.add_argument("--formula-col", type=str, default="formula", help="Name of the formula column.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (for reproducibility, though this task is deterministic).")
    
    args = parser.parse_args()
    
    if args.seed is not None:
        np.random.seed(args.seed)
        random.seed(args.seed)
    
    logger.info(f"Loading data from {args.input}")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows.")
    
    try:
        df_stratified = stratify_dataframe(df, formula_column=args.formula_col)
    except ValueError as e:
        logger.error(f"Stratification failed: {e}")
        sys.exit(1)
    
    save_stratified_data(df_stratified, args.output)
    logger.info("Stratification process completed successfully.")


if __name__ == "__main__":
    import argparse
    main()
