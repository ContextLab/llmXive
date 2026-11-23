"""
Generate the combinatorial library of hypothetical ABX3 perovskites.

Task T024: Generate combinatorial library using strictly defined sets
A={K, Rb, Cs}, B={Ti, Zr, Hf, Sn, Ge}, X={F, Cl, Br, I}.
Output: data/processed/hypothetical_library.csv
"""
import os
import sys
import itertools
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Strictly defined element sets per Constitution Principle VII
ELEMENTS_A = ["K", "Rb", "Cs"]
ELEMENTS_B = ["Ti", "Zr", "Hf", "Sn", "Ge"]
ELEMENTS_X = ["F", "Cl", "Br", "I"]

OUTPUT_PATH = project_root / "data" / "processed" / "hypothetical_library.csv"

def generate_combinatorial_library():
    """
    Generate all combinations of A, B, X elements for ABX3 perovskites.
    
    Returns:
        pd.DataFrame: DataFrame with columns ['formula', 'element_A', 'element_B', 'element_X']
    """
    logger.info(f"Generating combinatorial library with A={ELEMENTS_A}, B={ELEMENTS_B}, X={ELEMENTS_X}")
    
    combinations = list(itertools.product(ELEMENTS_A, ELEMENTS_B, ELEMENTS_X))
    
    logger.info(f"Total combinations generated: {len(combinations)}")
    
    data = []
    for a, b, x in combinations:
        # Formula is A B X3
        formula = f"{a}{b}{x}3"
        data.append({
            "formula": formula,
            "element_A": a,
            "element_B": b,
            "element_X": x
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Library DataFrame shape: {df.shape}")
    return df

def main():
    """Main entry point to generate and save the hypothetical library."""
    log_pipeline_event("Starting T024: Generate combinatorial library")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate the library
    df = generate_combinatorial_library()
    
    # Save to CSV
    df.to_csv(OUTPUT_PATH, index=False)
    
    logger.info(f"Saved hypothetical library to {OUTPUT_PATH}")
    log_pipeline_event(f"T024 complete: Generated {len(df)} candidates to {OUTPUT_PATH}")
    
    return df

if __name__ == "__main__":
    main()