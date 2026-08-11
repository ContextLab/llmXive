"""
Stratify the perovskite dataset by chemistry class (oxide, halide, nitride).

This module implements FR-014: Stratification by perovskite chemistry class.
It reads the cleaned, merged dataset, identifies the chemistry class based on
the anion element (O, F/Cl/Br/I, N), and splits the data into strata for
independent correlation analysis.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.validation import setup_logger, handle_error

logger = setup_logger("stratify", logging.INFO)

# Constants for chemistry classification
OXIDE_ANIONS = {'O', 'O2'}
HALIDE_ANIONS = {'F', 'Cl', 'Br', 'I', 'F-', 'Cl-', 'Br-', 'I-'}
NITRIDE_ANIONS = {'N', 'N3'}

# Expected columns from the cleaned dataset (produced by T013)
EXPECTED_COLUMNS = {
    'structure_id', 
    'formula', 
    'thermal_conductivity', 
    'temperature_K',
    'source_reference'
}

def classify_chemistry(formula: str) -> str:
    """
    Determine the chemistry class of a perovskite based on its formula.
    
    Args:
        formula: Chemical formula string (e.g., 'CaTiO3', 'CsPbCl3')
        
    Returns:
        One of: 'oxide', 'halide', 'nitride', or 'unknown'
    """
    if not isinstance(formula, str):
        return 'unknown'
        
    # Normalize formula to uppercase for comparison
    formula_upper = formula.upper()
    
    # Check for nitride (N)
    # Note: We must be careful not to match 'N' in other contexts if possible,
    # but in simple formula strings like 'CaTiO3' or 'CsPbCl3', 
    # 'N' usually denotes Nitrogen.
    if any(anion in formula_upper for anion in NITRIDE_ANIONS):
        return 'nitride'
        
    # Check for halides (F, Cl, Br, I)
    # Cl, Br, I are distinct; F is distinct
    if any(anion in formula_upper for anion in HALIDE_ANIONS):
        return 'halide'
        
    # Check for oxides (O)
    if any(anion in formula_upper for anion in OXIDE_ANIONS):
        return 'oxide'
        
    return 'unknown'

def stratify_dataframe(df: pd.DataFrame, formula_col: str = 'formula') -> Dict[str, pd.DataFrame]:
    """
    Split the dataframe into strata based on chemistry class.
    
    Args:
        df: Input dataframe with a 'formula' column
        formula_col: Name of the column containing chemical formulas
        
    Returns:
        Dictionary mapping chemistry class ('oxide', 'halide', 'nitride', 'unknown')
        to their respective DataFrames.
        
    Raises:
        ValueError: If the input dataframe is empty or missing required columns.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot stratify.")
        
    if formula_col not in df.columns:
        raise ValueError(f"Column '{formula_col}' not found in dataframe. Available: {list(df.columns)}")
        
    logger.info(f"Stratifying {len(df)} records by chemistry class...")
    
    strata = {}
    
    # Apply classification
    df['chemistry_class'] = df[formula_col].apply(classify_chemistry)
    
    # Group by class
    for class_name, group in df.groupby('chemistry_class'):
        strata[class_name] = group.copy()
        logger.info(f"  - {class_name}: {len(strata[class_name])} samples")
        
    # Validate minimums if necessary (though FR-014 doesn't specify a hard fail here,
    # it's good practice to log warnings for very small strata)
    for class_name, group in strata.items():
        if class_name != 'unknown' and len(group) < 5:
            logger.warning(f"Small sample size for {class_name}: {len(group)} samples. "
                         f"Statistical analysis may be unreliable.")
                           
    return strata

def save_stratified_data(strata: Dict[str, pd.DataFrame], output_dir: Path) -> List[str]:
    """
    Save each stratum to a separate CSV file.
    
    Args:
        strata: Dictionary of DataFrames by chemistry class
        output_dir: Directory to save the CSV files
        
    Returns:
        List of paths to the saved files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    
    for class_name, df in strata.items():
        # Sanitize filename
        safe_name = class_name.replace(' ', '_')
        file_path = output_dir / f"perovskite_{safe_name}_stratum.csv"
        
        # Drop the temporary chemistry_class column if it exists and isn't needed in output
        # or keep it for clarity. Let's keep it.
        df.to_csv(file_path, index=False)
        saved_files.append(str(file_path))
        logger.info(f"Saved {class_name} stratum to {file_path}")
        
    return saved_files

def main():
    """
    Main entry point for the stratification pipeline.
    
    Reads the cleaned data from data/cleaned/merged_perovskite.csv,
    stratifies it, and saves the results to data/cleaned/strata/.
    """
    # Define paths relative to project root
    input_path = project_root / "data" / "cleaned" / "merged_perovskite.csv"
    output_dir = project_root / "data" / "cleaned" / "strata"
    
    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}. " \
                    f"Please run the cleaning pipeline (T013) first."
        handle_error(error_msg, level="CRITICAL")
        sys.exit(1)
        
    try:
        # Load data
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        
        # Validate minimal schema (we expect more, but check essentials)
        required = ['formula', 'thermal_conductivity']
        missing = [col for col in required if col not in df.columns]
        if missing:
            error_msg = f"Missing required columns in input data: {missing}"
            handle_error(error_msg, level="CRITICAL")
            sys.exit(1)
            
        # Perform stratification
        strata = stratify_dataframe(df)
        
        # Check if we have any valid strata
        valid_classes = [k for k in strata.keys() if k != 'unknown']
        if not valid_classes:
            logger.warning("No valid chemistry classes identified. All data marked as 'unknown'.")
            # Still save the unknown group
            
        # Save results
        saved_files = save_stratified_data(strata, output_dir)
        
        # Create a summary report
        summary_path = output_dir / "stratification_summary.json"
        summary_data = {
            "total_records": len(df),
            "strata": {k: len(v) for k, v in strata.items()},
            "output_files": saved_files
        }
        
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
            
        logger.info(f"Stratification complete. Summary saved to {summary_path}")
        
    except Exception as e:
        handle_error(f"Error during stratification: {str(e)}", level="CRITICAL")
        sys.exit(1)

if __name__ == "__main__":
    main()
