import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from config import load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def normalize_element_symbol(symbol: str) -> str:
    """
    Normalizes elemental symbols to IUPAC standards (1-2 chars, capitalized).
    """
    if not symbol:
        return ""
    symbol = symbol.strip().upper()
    if len(symbol) == 1:
        return symbol
    elif len(symbol) == 2:
        return symbol[0] + symbol[1].lower()
    else:
        # Handle potential errors or non-standard inputs
        return symbol[:2].capitalize()

def parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parses a composition string or dict into a standardized dict.
    Expected formats:
    - JSON string: '{"Zr": 0.6, "Cu": 0.4}'
    - Dict object (if already parsed)
    - String like "Zr60Cu40" (simple parser for demo)
    """
    if isinstance(comp_str, dict):
        return {normalize_element_symbol(k): float(v) for k, v in comp_str.items()}
    
    try:
        # Try JSON
        return json.loads(comp_str)
    except (json.JSONDecodeError, TypeError):
        # Try simple parser "Zr60Cu40"
        # This is a fallback for malformed data
        elements = re.findall(r'([A-Z][a-z]?)(\d+(?:\.\d+)?)', str(comp_str))
        if not elements:
            return {}
        total = sum(float(e[1]) for e in elements)
        if total == 0:
            return {}
        return {normalize_element_symbol(e[0]): float(e[1])/total for e in elements}

def generate_synthetic_data(num_rows: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates synthetic metallic glass data for validation.
    Mimics 'dominant element' distribution if real data exists, else uniform.
    Uses linear mixing rule + Gaussian noise (σ=0.05).
    """
    import random as random_module
    random_module.seed(seed)
    np.random.seed(seed)

    # Mock densities
    mock_densities = {
        "Zr": 6.52, "Cu": 8.96, "Ni": 8.90, "Al": 2.70,
        "Fe": 7.87, "Ti": 4.51, "Pd": 12.02, "Pt": 21.45,
        "La": 6.15, "Ce": 6.77, "Mg": 1.74, "Ca": 1.55
    }
    elements = list(mock_densities.keys())

    data = []
    for _ in range(num_rows):
        # Random composition
        num_elems = random_module.randint(2, 5)
        selected = random_module.sample(elements, num_elems)
        weights = [random_module.random() for _ in selected]
        total_weight = sum(weights)
        comp = {e: w/total_weight for e, w in zip(selected, weights)}
        
        # Calculate density
        baseline = sum(w * mock_densities[e] for e, w in comp.items())
        noise = np.random.normal(0, 0.05)
        density = baseline + noise
        
        data.append({
            "composition": comp,
            "density": float(density)
        })
    return data

def preprocess_data(input_path: Path, output_path: Path, min_rows: int = 50) -> bool:
    """
    Preprocesses data: normalizes symbols, filters missing density.
    Returns True if real data is sufficient, False if fallback triggered.
    
    Strategy: Filter rows with missing density values.
    Critical Logic: If filtering reduces the row count to < 50, the system MUST 
    immediately trigger 'Pipeline Validation Mode' (synthetic generation) as per FR-001.
    """
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found.")
        return False

    df = pd.read_csv(input_path)

    # Normalize composition column if it's a string
    if 'composition' in df.columns:
        # Parse and normalize composition strings to ensure IUPAC standards
        # We store the normalized composition as a JSON string
        def normalize_comp(comp_val):
            parsed = parse_composition(comp_val)
            return json.dumps(parsed)
        
        df['composition'] = df['composition'].apply(normalize_comp)

    # Filter rows with missing density
    initial_count = len(df)
    df = df.dropna(subset=['density'])
    final_count = len(df)

    logger.info(f"Filtered {initial_count - final_count} rows with missing density.")

    if final_count < min_rows:
        logger.warning(f"E_DATA_INSUFFICIENT: Only {final_count} rows remain (min: {min_rows}). Triggering synthetic generation.")
        return False

    # Save clean data
    df.to_csv(output_path, index=False)
    logger.info(f"Saved clean data to {output_path} with {final_count} rows.")
    return True

def main():
    """
    Main entry point for preprocessing.
    """
    config = load_config()
    data_dir = config.data_dir
    raw_data_path = data_dir / "raw_data.csv"
    clean_data_path = data_dir / "clean_data.csv"
    synthetic_data_path = data_dir / "synthetic_data.csv"

    data_dir.mkdir(parents=True, exist_ok=True)

    # Preprocess real data
    is_sufficient = preprocess_data(raw_data_path, clean_data_path, min_rows=50)

    if not is_sufficient:
        # Generate synthetic data
        logger.info("Generating synthetic data due to insufficient real data.")
        synthetic_data = generate_synthetic_data(num_rows=100, seed=42)
        
        # Save synthetic data
        rows = []
        for item in synthetic_data:
            rows.append({
                "composition": json.dumps(item["composition"]),
                "density": item["density"]
            })
        df_synthetic = pd.DataFrame(rows)
        df_synthetic.to_csv(synthetic_data_path, index=False)
        logger.info(f"Saved synthetic data to {synthetic_data_path} with {len(df_synthetic)} rows.")
        # Ensure the output path points to the synthetic data if fallback was triggered
        # The calling logic (T015) will check for the existence of either file.

if __name__ == "__main__":
    main()