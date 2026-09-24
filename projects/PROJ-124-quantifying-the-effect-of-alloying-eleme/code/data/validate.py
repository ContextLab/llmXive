import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
import pandas as pd
from config.elements import get_abundant_elements_set
from utils.logger import get_logger

def validate_elements(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate elements in the dataframe against the known abundant elements set.
    
    This function implements the validation logic for T016:
    1. Identifies rows with unknown elements (elements not in the abundant set).
    2. Logs specific warnings for each excluded element/composition.
    3. Filters out rows containing unknown elements.
    4. Returns statistics about the exclusion process.
    
    Args:
        df: Input DataFrame with a 'composition' column containing strings like "Fe50Ni30Co20".
        logger: Optional logger instance. If None, creates a default logger.
        
    Returns:
        Tuple containing:
            - Filtered DataFrame with only valid rows.
            - Dictionary with validation statistics:
                - 'total_rows': Total rows in input.
                - 'excluded_rows': Number of rows removed.
                - 'valid_rows': Number of rows kept.
                - 'excluded_compositions': List of excluded composition strings.
                - 'unknown_elements_found': Set of unique unknown elements found.
    """
    if logger is None:
        logger = get_logger("validate_elements")
    
    abundant_elements = get_abundant_elements_set()
    original_count = len(df)
    excluded_compositions = []
    unknown_elements_found: Set[str] = set()
    
    def extract_elements(composition_str: str) -> List[str]:
        """Extract element symbols from a composition string (e.g., "Fe50Ni30" -> ["Fe", "Ni"])."""
        import re
        # Match element symbols (one or two letters, first uppercase)
        elements = re.findall(r'([A-Z][a-z]?)', composition_str)
        return elements
    
    def is_row_valid(row: pd.Series) -> bool:
        """Check if a row contains only known abundant elements."""
        composition = str(row['composition'])
        elements = extract_elements(composition)
        
        for elem in elements:
            if elem not in abundant_elements:
                unknown_elements_found.add(elem)
                return False
        return True
    
    # Identify valid rows
    valid_mask = df.apply(is_row_valid, axis=1)
    valid_count = valid_mask.sum()
    excluded_count = original_count - valid_count
    
    # Log specific warnings for excluded rows
    if excluded_count > 0:
        excluded_df = df[~valid_mask]
        for idx, row in excluded_df.iterrows():
            composition = str(row['composition'])
            elements = extract_elements(composition)
            unknowns = [e for e in elements if e not in abundant_elements]
            
            logger.warning(
                f"Excluding row {idx}: composition '{composition}' contains unknown elements: {unknowns}"
            )
        
        # Log summary
        logger.warning(
            f"Validation complete: Excluded {excluded_count} rows containing unknown elements. "
            f"Unknown elements found: {sorted(unknown_elements_found)}"
        )
    else:
        logger.info("Validation complete: No rows excluded. All compositions contain known abundant elements.")
    
    # Filter the dataframe
    filtered_df = df[valid_mask].reset_index(drop=True)
    
    # Compile statistics
    stats = {
        'total_rows': original_count,
        'excluded_rows': excluded_count,
        'valid_rows': valid_count,
        'excluded_compositions': excluded_df['composition'].tolist() if excluded_count > 0 else [],
        'unknown_elements_found': sorted(list(unknown_elements_found))
    }
    
    return filtered_df, stats

def main():
    """
    Main entry point for the validation script.
    Reads the intermediate features dataset, validates elements,
    logs warnings, and saves the final processed dataset.
    """
    logger = get_logger("validate_main")
    logger.info("Starting element validation process (T016)...")
    
    # Define paths
    input_path = Path("data/processed/features_intermediate.csv")
    output_path = Path("data/processed/features.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T015 (feature engineering) has been completed successfully.")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading intermediate features from {input_path}...")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Perform validation
    logger.info("Validating elements against abundant set...")
    filtered_df, stats = validate_elements(df, logger)
    
    # Log statistics
    logger.info(f"Validation Statistics:")
    logger.info(f"  - Total rows: {stats['total_rows']}")
    logger.info(f"  - Excluded rows: {stats['excluded_rows']}")
    logger.info(f"  - Valid rows: {stats['valid_rows']}")
    if stats['unknown_elements_found']:
        logger.info(f"  - Unknown elements: {stats['unknown_elements_found']}")
    
    # Save final processed dataset
    logger.info(f"Saving validated dataset to {output_path}...")
    filtered_df.to_csv(output_path, index=False)
    
    # Verify output
    if output_path.exists():
        saved_df = pd.read_csv(output_path)
        logger.info(f"Successfully saved {len(saved_df)} rows to {output_path}")
        
        # Verify no nulls in critical columns if they exist
        critical_cols = ['atomic_radius', 'electronegativity', 'VEC_raw', 'VEC_avg']
        for col in critical_cols:
            if col in saved_df.columns:
                null_count = saved_df[col].isnull().sum()
                if null_count > 0:
                    logger.warning(f"Column '{col}' contains {null_count} null values in the output.")
                else:
                    logger.info(f"Column '{col}' has no null values.")
    else:
        logger.error(f"Failed to create output file: {output_path}")
        raise RuntimeError(f"Output file was not created: {output_path}")
    
    logger.info("Element validation process (T016) completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
