"""
Stratification utilities for perovskite data analysis.
Implements deterministic seed handling for any sampling.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import seed manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import init_seed, get_seed, add_seed_argument

def setup_logger_module(name: str = "stratify", level: int = logging.INFO) -> logging.Logger:
    """Setup a module-specific logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger_module()

def classify_chemistry(formula: str) -> str:
    """
    Classify perovskite chemistry class based on formula.

    Args:
        formula: Chemical formula string

    Returns:
        Class name: 'oxide', 'halide', 'nitride', or 'unknown'
    """
    formula_lower = formula.lower()
    if 'o' in formula_lower and 'x' not in formula_lower:
        return 'oxide'
    elif 'f' in formula_lower or 'cl' in formula_lower or 'br' in formula_lower or 'i' in formula_lower:
        return 'halide'
    elif 'n' in formula_lower and 'no' not in formula_lower:
        return 'nitride'
    return 'unknown'

def stratify_dataframe(df: pd.DataFrame, strategy_col: str = 'chemistry_class', seed: int = 42) -> pd.DataFrame:
    """
    Stratify dataframe by chemistry class.

    Args:
        df: Input dataframe
        strategy_col: Column to stratify by
        seed: Random seed

    Returns:
        Dataframe with stratification labels
    """
    init_seed(seed)
    logger.info(f"Stratifying by '{strategy_col}' with seed={seed}")
    
    if strategy_col not in df.columns:
        # Auto-classify if column missing
        df = df.copy()
        df[strategy_col] = df['formula'].apply(classify_chemistry)
    
    return df

def save_stratified_data(df: pd.DataFrame, output_path: str) -> None:
    """Save stratified data to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved stratified data to {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stratify perovskite data")
    parser = add_seed_argument(parser)
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    
    args = parser.parse_args()
    
    df = pd.read_csv(args.input)
    df_strat = stratify_dataframe(df, seed=args.seed)
    save_stratified_data(df_strat, args.output)
    sys.exit(0)

if __name__ == "__main__":
    main()
