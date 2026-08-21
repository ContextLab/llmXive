import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from config import Config, load_config
from utils.logger import get_logger

# Constants for logging
LOG_PREFIX = "LOG"
ERROR_PREFIX = "E_DATA_INSUFFICIENT"

def normalize_element_symbol(symbol: str) -> Optional[str]:
    """
    Normalize elemental symbols to IUPAC standards (1-2 chars).
    Returns None if the symbol is invalid or cannot be normalized.
    """
    if not symbol:
        return None
    symbol = symbol.strip().title()
    if len(symbol) == 1:
        if symbol.isalpha():
            return symbol
        return None
    if len(symbol) == 2:
        if symbol[0].isupper() and symbol[1].islower():
            return symbol
        return None
    # Attempt to extract valid 2-char symbol if longer string provided
    match = re.match(r'^([A-Z][a-z]?)', symbol)
    if match:
        return match.group(1)
    return None

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string into a dictionary of element: fraction.
    Expected format: "Element1:0.5,Element2:0.5" or similar.
    """
    composition = {}
    if not composition_str or not isinstance(composition_str, str):
        return composition

    parts = composition_str.split(',')
    for part in parts:
        if ':' in part:
            try:
                elem, frac = part.split(':')
                elem = normalize_element_symbol(elem)
                if elem:
                    composition[elem] = float(frac)
            except (ValueError, IndexError):
                continue
    return composition

def generate_synthetic_data(n_rows: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic metallic glass data.
    Uses a fixed seed for reproducibility.
    Mimics 'dominant element' distribution if real data exists, else uniform.
    """
    np.random.seed(seed)
    elements = ['Fe', 'Zr', 'Cu', 'Ni', 'Ti', 'Al', 'Mg', 'Y', 'La']
    data = []

    for _ in range(n_rows):
        n_elems = np.random.randint(2, 5)
        selected = np.random.choice(elements, n_elems, replace=False)
        weights = np.random.random(n_elems)
        weights /= weights.sum()

        composition = {str(e): float(w) for e, w in zip(selected, weights)}
        # Simple linear mixing rule + noise for density
        # Approximate densities: Fe=7.8, Zr=6.5, Cu=8.9, Ni=8.9, Ti=4.5, Al=2.7, Mg=1.7, Y=4.5, La=6.1
        elem_dens = {'Fe': 7.8, 'Zr': 6.5, 'Cu': 8.9, 'Ni': 8.9, 'Ti': 4.5, 'Al': 2.7, 'Mg': 1.7, 'Y': 4.5, 'La': 6.1}
        density = sum(composition[e] * elem_dens.get(e, 6.0) for e in composition)
        density += np.random.normal(0, 0.05)

        data.append({
            'composition': json.dumps(composition),
            'density': round(density, 4)
        })

    return pd.DataFrame(data)

def preprocess_data(
    raw_data_path: Path,
    clean_data_path: Path,
    synthetic_data_path: Path,
    validation_log_path: Path,
    config: Config
) -> Dict[str, Any]:
    """
    Preprocess raw data: filter missing densities, normalize symbols.
    Checks row count. If insufficient, triggers synthetic data generation.
    Updates validation_log.json with source selection and status.
    """
    logger = get_logger(__name__)
    status = "REAL"
    source = "raw"
    row_count = 0
    synthetic_required = False

    # Load raw data
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        synthetic_required = True
    else:
        try:
            df = pd.read_csv(raw_data_path)
            # Filter rows with missing density values
            df = df.dropna(subset=['density'])
            # Normalize composition symbols
            if 'composition' in df.columns:
                df['composition'] = df['composition'].apply(
                    lambda x: json.dumps(parse_composition(x)) if pd.notna(x) else None
                )
                df = df.dropna(subset=['composition'])

            row_count = len(df)

            if row_count < 50:
                logger.warning(f"Filtered data has {row_count} rows (< 50). Insufficient for training.")
                synthetic_required = True
            else:
                # Save clean data
                df.to_csv(clean_data_path, index=False)
                logger.info(f"Clean data saved to {clean_data_path} with {row_count} rows.")
        except Exception as e:
            logger.error(f"Error processing raw data: {e}")
            synthetic_required = True

    # Handle Synthetic Fallback
    if synthetic_required:
        source = "synthetic"
        status = "SYNTHETIC_REQUIRED"
        logger.warning(f"{ERROR_PREFIX}: Data source insufficient. Switching to synthetic mode.")
        
        # Generate synthetic data
        df_synthetic = generate_synthetic_data(n_rows=100, seed=42)
        df_synthetic.to_csv(synthetic_data_path, index=False)
        row_count = len(df_synthetic)
        logger.info(f"Synthetic data saved to {synthetic_data_path} with {row_count} rows.")

    # Update Validation Log
    log_entry = {
        "source": source,
        "status": status,
        "row_count": row_count,
        "clean_data_path": str(clean_data_path),
        "synthetic_data_path": str(synthetic_data_path),
        "message": f"Data source selected: {source} | Rows: {row_count} | Status: {status}"
    }
    
    # Log the specific format required by T016
    logger.info(f"{LOG_PREFIX}: Data source selected: {source} | Rows: {row_count} | Status: {status}")
    
    if synthetic_required:
        logger.warning(f"{ERROR_PREFIX}: Insufficient real data. Using synthetic data.")

    with open(validation_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)

    return log_entry

def main():
    config = load_config()
    raw_path = config.data_dir / "raw_data.csv"
    clean_path = config.data_dir / "clean_data.csv"
    synthetic_path = config.data_dir / "synthetic_data.csv"
    log_path = config.data_dir / "validation_log.json"

    # Ensure directories exist
    config.data_dir.mkdir(parents=True, exist_ok=True)

    result = preprocess_data(
        raw_data_path=raw_path,
        clean_data_path=clean_path,
        synthetic_data_path=synthetic_path,
        validation_log_path=log_path,
        config=config
    )
    
    print(f"Preprocessing complete. Status: {result['status']}, Rows: {result['row_count']}")

if __name__ == "__main__":
    main()