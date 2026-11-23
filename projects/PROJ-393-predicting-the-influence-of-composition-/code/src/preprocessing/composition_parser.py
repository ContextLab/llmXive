import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from src.utils.logging_config import setup_logging, create_logger
import sys
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)

def parse_formula_to_fractions(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula string (e.g., "Co2MnGa") into atomic fractions.
    Returns a dict of element -> fraction.
    """
    if not isinstance(formula, str) or not formula:
        return {}
    
    # Regex to match element symbols and optional counts
    # Matches: Element (Capital + optional lowercase) followed by optional number
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)
    
    if not matches:
        logger.warning(f"Could not parse formula: {formula}")
        return {}
    
    total_atoms = 0
    elements = {}
    
    for elem, count_str in matches:
        count = int(count_str) if count_str else 1
        elements[elem] = count
        total_atoms += count
    
    if total_atoms == 0:
        return {}
    
    fractions = {elem: count / total_atoms for elem, count in elements.items()}
    return fractions

def parse_composition(composition: str) -> Dict[str, float]:
    """Parse a single composition string."""
    return parse_formula_to_fractions(composition)

def parse_batch_compositions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse compositions in a DataFrame and add fractional columns.
    Adds columns: 'Co_frac', 'Mn_frac', etc.
    """
    if df.empty:
        return df
    
    logger.info("Parsing batch compositions...")
    
    if 'composition' not in df.columns:
        logger.warning("No 'composition' column found.")
        return df
    
    # Collect all unique elements first
    all_elements = set()
    for comp in df['composition']:
        if pd.isna(comp): continue
        parsed = parse_formula_to_fractions(str(comp))
        all_elements.update(parsed.keys())
    
    # Add columns for each element
    for elem in all_elements:
        col_name = f"{elem}_frac"
        df[col_name] = 0.0
    
    # Fill fractions
    for idx, row in df.iterrows():
        comp = row['composition']
        if pd.isna(comp):
            continue
        parsed = parse_formula_to_fractions(str(comp))
        for elem, frac in parsed.items():
            col_name = f"{elem}_frac"
            if col_name in df.columns:
                df.at[idx, col_name] = round(frac, 4)
    
    logger.info(f"Parsed {len(all_elements)} unique elements.")
    return df

def main():
    setup_logging()
    logger.info("Composition Parser Main Entry")
    return 0

if __name__ == "__main__":
    sys.exit(main())