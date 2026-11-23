import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def normalize_element_symbol(symbol: str) -> str:
    """
    Normalize elemental symbols to IUPAC standards (1-2 chars, capital first).
    """
    symbol = symbol.strip()
    if len(symbol) == 0:
        return ""
    if len(symbol) == 1:
        return symbol.upper()
    return symbol[0].upper() + symbol[1].lower()

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe50Ni40B10' into a dict of element: fraction.
    Handles formats: 'Fe50Ni40B10', 'Fe:50, Ni:40, B:10', etc.
    """
    if not composition_str:
        return {}

    # Normalize separators
    composition_str = composition_str.replace(":", " ").replace(",", " ")
    parts = composition_str.split()

    result = {}
    for part in parts:
        match = re.match(r'^([A-Z][a-z]?)(\d+\.?\d*)$', part)
        if match:
            element = normalize_element_symbol(match.group(1))
            try:
                fraction = float(match.group(2))
                if element:
                    result[element] = fraction
            except ValueError:
                logger.warning(f"Invalid numeric fraction in: {part}")
        else:
            logger.warning(f"Could not parse composition part: {part}")

    return result

def generate_synthetic_data(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic metallic glass data.
    Uses a fixed seed for reproducibility.
    Mimics 'dominant element' distribution if real data exists (checked via validation_log).
    """
    np.random.seed(seed)
    elements = ['Fe', 'Ni', 'Cu', 'Zr', 'Ti', 'Al', 'Mg', 'B', 'Si']
    rows = []

    for _ in range(n_samples):
        # Random composition
        n_elements = np.random.randint(2, 5)
        selected = np.random.choice(elements, n_elements, replace=False)
        fractions = np.random.rand(n_elements)
        fractions /= fractions.sum()

        composition = {elem: float(f) for elem, f in zip(selected, fractions)}
        composition_str = "".join([f"{k}{int(v*100)}" for k, v in composition.items()])

        # Linear mixing rule + noise (simplified density model)
        # Approximate densities: Fe=7.87, Ni=8.9, Cu=8.96, Zr=6.52, Ti=4.5, Al=2.7, Mg=1.74, B=2.34, Si=2.33
        density_map = {
            'Fe': 7.87, 'Ni': 8.90, 'Cu': 8.96, 'Zr': 6.52, 'Ti': 4.50,
            'Al': 2.70, 'Mg': 1.74, 'B': 2.34, 'Si': 2.33
        }
        base_density = sum(fractions[i] * density_map[selected[i]] for i in range(n_elements))
        noise = np.random.normal(0, 0.05 * base_density)
        density = max(0.1, base_density + noise)

        rows.append({
            'composition': composition_str,
            'composition_dict': json.dumps(composition),
            'density': density
        })

    return pd.DataFrame(rows)

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows with missing density values and normalize composition strings.
    """
    logger.info(f"Starting preprocessing on {len(df)} rows")

    # Filter missing density
    df = df.dropna(subset=['density'])
    logger.info(f"Filtered to {len(df)} rows with valid density")

    # Normalize composition
    if 'composition' in df.columns:
        df['composition'] = df['composition'].apply(
            lambda x: "".join([f"{k}{int(v*100)}" for k, v in parse_composition(x).items()])
        )

    return df

def main():
    """
    Orchestrate data preprocessing and validation.
    Checks if real data is sufficient. If not, flags for synthetic generation.
    """
    config = load_config()
    data_dir = config.data_dir
    raw_path = data_dir / "raw_data.csv"
    clean_path = data_dir / "clean_data.csv"
    validation_log_path = data_dir / "validation_log.json"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    source_status = "REAL"
    row_count = 0
    data_source = "none"

    # Try to load real data
    if raw_path.exists():
        try:
            df = pd.read_csv(raw_path)
            df = preprocess_data(df)
            df.to_csv(clean_path, index=False)
            row_count = len(df)
            data_source = str(clean_path)
            logger.info(f"Real data processed: {row_count} rows saved to {clean_path}")
        except Exception as e:
            logger.error(f"Failed to process real data: {e}")
            source_status = "REAL_FAILED"
    else:
        source_status = "REAL_MISSING"

    # Check sufficiency
    if row_count < 50:
        logger.warning("E_DATA_INSUFFICIENT: Real data has fewer than 50 rows.")
        source_status = "SYNTHETIC_REQUIRED"

    # Log data source selection
    if source_status == "SYNTHETIC_REQUIRED":
        logger.warning("Switching to synthetic mode due to insufficient real data.")
        # Generate synthetic data
        synthetic_df = generate_synthetic_data(n_samples=100)
        synthetic_df.to_csv(data_dir / "synthetic_data.csv", index=False)
        data_source = str(data_dir / "synthetic_data.csv")
        row_count = len(synthetic_df)
        source_status = "SYNTHETIC"
        logger.warning("E_DATA_INSUFFICIENT: Synthetic data generated.")

    # Final log format: LOG: Data source selected: {source} | Rows: {count} | Status: {status}
    log_message = f"Data source selected: {data_source} | Rows: {row_count} | Status: {source_status}"
    logger.info(log_message)

    # Write validation log
    validation_log = {
        "source_status": source_status,
        "row_count": row_count,
        "data_source": data_source,
        "message": log_message
    }
    with open(validation_log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)

    logger.info(f"Validation log written to {validation_log_path}")

if __name__ == "__main__":
    main()