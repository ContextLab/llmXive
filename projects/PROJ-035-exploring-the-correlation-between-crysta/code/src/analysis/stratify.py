import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import seed manager for deterministic operations if needed
try:
    from src.utils.seed_manager import init_seed, get_seed
except ImportError:
    # Fallback if seed manager is not available or path differs
    def init_seed(seed: int = 42):
        np.random.seed(seed)
        return seed
    def get_seed():
        return 42

LOGGER_NAME = "stratify_module"

def setup_logger_module(name: str = LOGGER_NAME, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger for the stratify module.
    
    Args:
        name: Logger name.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger_module()

def classify_chemistry(formula: str) -> str:
    """
    Classifies the chemistry class of a perovskite based on its formula string.
    Expected format: ABX3 or similar, e.g., 'CaTiO3', 'CsPbI3'.
    
    Logic:
    - Oxide: Contains 'O' and no halogens (F, Cl, Br, I) or N as the primary anion.
    - Halide: Contains F, Cl, Br, or I.
    - Nitride: Contains 'N' and no halogens.
    
    Args:
        formula: Chemical formula string (e.g., 'CaTiO3').
        
    Returns:
        String classification: 'oxide', 'halide', 'nitride', or 'unknown'.
    """
    if not isinstance(formula, str) or pd.isna(formula):
        return 'unknown'
    
    formula = formula.strip()
    if not formula:
        return 'unknown'
    
    # Simple heuristic based on element symbols present in the formula string
    # This assumes the formula string is clean (e.g., "CaTiO3", not "Ca Ti O 3")
    has_halogens = any(hal in formula for hal in ['F', 'Cl', 'Br', 'I'])
    has_oxygen = 'O' in formula
    has_nitrogen = 'N' in formula
    
    if has_halogens:
        return 'halide'
    elif has_nitrogen and not has_oxygen:
        return 'nitride'
    elif has_oxygen:
        return 'oxide'
    else:
        return 'unknown'

def stratify_dataframe(df: pd.DataFrame, class_column: str = 'chemistry_class') -> Dict[str, pd.DataFrame]:
    """
    Stratifies a DataFrame by the chemistry class column.
    
    Args:
        df: Input DataFrame containing perovskite data.
        class_column: Name of the column containing chemistry class labels.
        
    Returns:
        Dictionary mapping class names to their respective DataFrames.
        
    Raises:
        ValueError: If the class_column is missing or if no valid classes are found.
    """
    if class_column not in df.columns:
        logger.error(f"Column '{class_column}' not found in DataFrame. Available columns: {list(df.columns)}")
        raise ValueError(f"Column '{class_column}' not found in DataFrame.")
    
    # Ensure the column is string type for consistent processing
    df[class_column] = df[class_column].astype(str)
    
    # Filter out unknown/empty classes if necessary, or keep them as a separate group
    # For this task, we focus on 'oxide', 'halide', 'nitride'
    valid_classes = ['oxide', 'halide', 'nitride']
    
    stratified_data = {}
    for cls in valid_classes:
        subset = df[df[class_column] == cls].copy()
        if not subset.empty:
            stratified_data[cls] = subset
            logger.info(f"Stratified '{cls}': {len(subset)} rows")
        else:
            logger.warning(f"No data found for chemistry class: '{cls}'")
    
    if not stratified_data:
        raise ValueError("No valid data found for any expected chemistry classes (oxide, halide, nitride).")
    
    return stratified_data

def save_stratified_data(stratified_data: Dict[str, pd.DataFrame], output_dir: str, seed: Optional[int] = None) -> List[str]:
    """
    Saves stratified DataFrames to CSV files in the specified directory.
    
    Args:
        stratified_data: Dictionary of class_name -> DataFrame.
        output_dir: Directory path to save the CSV files.
        seed: Optional seed for reproducibility (not strictly needed for saving, but good practice).
        
    Returns:
        List of paths to the saved files.
    """
    if seed is not None:
        init_seed(seed)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for cls, data in stratified_data.items():
        filename = f"stratified_{cls}.csv"
        file_path = output_path / filename
        data.to_csv(file_path, index=False)
        saved_files.append(str(file_path))
        logger.info(f"Saved {cls} data to {file_path}")
    
    return saved_files

def main():
    """
    Main entry point for the stratification script.
    Reads the cleaned merged dataset, classifies chemistry, stratifies, and saves results.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stratify perovskite data by chemistry class.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input merged CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to the output directory for stratified CSVs.")
    parser.add_argument("--class-column", type=str, default="chemistry_class", help="Column name for chemistry class.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    logger.info(f"Starting stratification process.")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output directory: {args.output}")
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows from {args.input}")
        
        # If the chemistry_class column is missing, we might need to derive it.
        # However, based on the task description and typical pipeline flow,
        # T015 (clean_merge) should have produced this column or T021 (descriptors)
        # might have added it. If it's missing, we attempt to classify based on a formula column.
        if args.class_column not in df.columns:
            logger.warning(f"Column '{args.class_column}' not found. Attempting to derive from 'formula' if available.")
            if 'formula' in df.columns:
                df[args.class_column] = df['formula'].apply(classify_chemistry)
                logger.info("Derived chemistry_class from 'formula' column.")
            else:
                logger.error(f"Cannot find column '{args.class_column}' or 'formula' to derive it.")
                sys.exit(1)
        
        stratified_data = stratify_dataframe(df, class_column=args.class_column)
        saved_files = save_stratified_data(stratified_data, args.output, seed=args.seed)
        
        logger.info(f"Stratification complete. Saved {len(saved_files)} files.")
        for f in saved_files:
            print(f)
            
    except Exception as e:
        logger.error(f"Error during stratification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
