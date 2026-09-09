import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import seed utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import init_seed, add_seed_argument

def setup_logger_module(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module(__name__)

def classify_chemistry(formula: str) -> str:
    """Classify perovskite chemistry class (oxide, halide, nitride)."""
    formula_lower = formula.lower()
    if 'o' in formula_lower:
        return 'oxide'
    elif 'cl' in formula_lower or 'br' in formula_lower or 'i' in formula_lower:
        return 'halide'
    elif 'n' in formula_lower:
        return 'nitride'
    return 'unknown'

def stratify_dataframe(df: pd.DataFrame, seed: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    """Stratify dataframe by chemistry class."""
    init_seed(seed)
    
    df = df.copy()
    df['chemistry_class'] = df['formula'].apply(classify_chemistry)
    
    stratified = {}
    for class_name, group in df.groupby('chemistry_class'):
        stratified[class_name] = group.reset_index(drop=True)
    
    return stratified

def save_stratified_data(stratified_data: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Save stratified data to separate CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for class_name, df in stratified_data.items():
        out_path = output_dir / f"stratified_{class_name}.csv"
        df.to_csv(out_path, index=False)
        logger.info(f"Saved {class_name} data to {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Stratify Perovskite Data")
    add_seed_argument(parser)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    
    init_seed(args.seed)
    
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    df = pd.read_csv(args.input)
    stratified = stratify_dataframe(df, seed=args.seed)
    save_stratified_data(stratified, args.output_dir)

if __name__ == "__main__":
    main()
