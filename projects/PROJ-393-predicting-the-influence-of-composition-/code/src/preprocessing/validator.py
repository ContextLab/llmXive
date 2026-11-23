import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import pandas as pd
from src.utils.logging_config import setup_logging, create_logger
from src.utils.periodic_table_loader import load_elemental_properties
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)

def extract_elements_from_composition(composition: str) -> List[str]:
    if not isinstance(composition, str):
        return []
    # Regex to find element symbols (Capital + optional lowercase)
    return re.findall(r'[A-Z][a-z]?', composition)

def validate_compositions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates compositions against the periodic table.
    Logs warnings for unknown elements but does not crash.
    """
    if df.empty:
        return df
    
    logger.info("Validating compositions against periodic table...")
    periodic_table = load_elemental_properties()
    known_elements = set(periodic_table['element'].tolist())
    
    unknown_elements = set()
    
    if 'composition' not in df.columns:
        logger.warning("No 'composition' column found to validate.")
        return df
    
    for idx, row in df.iterrows():
        comp = row['composition']
        if pd.isna(comp):
            continue
        
        elements = extract_elements_from_composition(str(comp))
        for elem in elements:
            if elem not in known_elements:
                unknown_elements.add(elem)
    
    if unknown_elements:
        logger.warning(f"Found {len(unknown_elements)} unknown elements: {unknown_elements}")
        # Log specific rows if needed, but for now just the set
    else:
        logger.info("All compositions validated successfully.")
    
    return df

def main():
    setup_logging()
    logger.info("Validator Main Entry")
    # This is a utility function usually called by the pipeline
    return 0

if __name__ == "__main__":
    sys.exit(main())