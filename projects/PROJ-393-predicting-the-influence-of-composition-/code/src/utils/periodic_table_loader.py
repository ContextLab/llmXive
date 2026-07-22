import csv
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from src.utils.logging_config import setup_logging, log_checksum
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)
DATA_FILE = project_root / "data" / "raw" / "elemental_properties.csv"

def load_elemental_properties() -> pd.DataFrame:
    """
    Load elemental properties from CSV.
    Returns an empty DataFrame if file is missing or invalid.
    """
    import pandas as pd
    
    if not DATA_FILE.exists():
        logger.error(f"Elemental properties file not found: {DATA_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(DATA_FILE)
        # Validate columns
        required = ['element', 'electronegativity', 'atomic_radii', 'valence_electrons']
        missing = [col for col in required if col not in df.columns]
        if missing:
            logger.error(f"Missing required columns in elemental properties: {missing}")
            return pd.DataFrame()
        
        # Convert numeric columns, coercing errors to NaN
        numeric_cols = ['electronegativity', 'atomic_radii', 'valence_electrons']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"Loaded {len(df)} elements from {DATA_FILE}")
        return df
    except Exception as e:
        logger.error(f"Error loading elemental properties: {e}")
        return pd.DataFrame()

def get_element_property(element: str, property_name: str) -> Optional[Any]:
    """Get a specific property for an element."""
    df = load_elemental_properties()
    if df.empty:
        return None
    row = df[df['element'] == element]
    if row.empty:
        return None
    val = row[property_name].values[0]
    return val if not pd.isna(val) else None

def get_all_elements() -> List[str]:
    df = load_elemental_properties()
    if df.empty:
        return []
    return df['element'].tolist()

def validate_elements_in_dataset(elements: List[str]) -> Tuple[List[str], List[str]]:
    """Returns (known, unknown) elements."""
    all_known = set(get_all_elements())
    known = [e for e in elements if e in all_known]
    unknown = [e for e in elements if e not in all_known]
    return known, unknown

def main():
    setup_logging()
    logger.info("Periodic Table Loader Main Entry")
    df = load_elemental_properties()
    if not df.empty:
        logger.info(f"Periodic table loaded with {len(df)} entries.")
    return 0

if __name__ == "__main__":
    sys.exit(main())