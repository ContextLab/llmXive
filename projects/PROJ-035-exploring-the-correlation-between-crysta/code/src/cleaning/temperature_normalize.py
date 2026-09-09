import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
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

def slack_normalization_factor(T_ref: float, T: float) -> float:
    """
    Calculate normalization factor based on Slack (1979).
    k(T) = k_ref * (T_ref / T)^1.0
    Returns the factor (T_ref / T)^1.0
    """
    if T == 0:
        raise ValueError("Temperature cannot be zero.")
    return (T_ref / T) ** 1.0

def is_within_reference_window(T: float, T_ref: float = 300.0, tolerance: float = 10.0) -> bool:
    """Check if temperature is within T_ref +/- tolerance."""
    return abs(T - T_ref) <= tolerance

def normalize_thermal_conductivity(k: float, T: float, T_ref: float = 300.0) -> float:
    """Normalize thermal conductivity to reference temperature."""
    if is_within_reference_window(T, T_ref):
        return k
    factor = slack_normalization_factor(T_ref, T)
    return k * factor

def normalize_dataframe(df: pd.DataFrame, T_col: str = 'temperature', k_col: str = 'thermal_conductivity') -> pd.DataFrame:
    """Apply normalization to the dataframe."""
    df = df.copy()
    df['normalized_k'] = df.apply(
        lambda row: normalize_thermal_conductivity(row[k_col], row[T_col]) 
        if pd.notna(row[T_col]) else None, 
        axis=1
    )
    return df

def apply_temperature_normalization(input_path: Path, output_path: Path, seed: Optional[int] = None) -> None:
    """
    Main entry point for temperature normalization.
    Ensures deterministic behavior via seed.
    """
    init_seed(seed)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    
    # Example of deterministic filtering if seed is provided
    if seed is not None:
        np.random.seed(seed)
        # In a real scenario, this might filter borderline cases deterministically
        # mask = np.random.rand(len(df)) > 0.0 
        # df = df[mask]
    
    df_normalized = normalize_dataframe(df)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_normalized.to_csv(output_path, index=False)
    logger.info(f"Normalized data saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Normalize Thermal Conductivity")
    add_seed_argument(parser)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    
    init_seed(args.seed)
    apply_temperature_normalization(args.input, args.output, seed=args.seed)

if __name__ == "__main__":
    main()
