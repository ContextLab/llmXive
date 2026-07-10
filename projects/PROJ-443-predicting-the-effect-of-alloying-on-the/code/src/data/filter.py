"""
Filtering logic for High-Entropy Alloy (HEA) data.

Retains samples with:
1. >= 5 principal elements
2. Valid (non-null) Bulk Modulus values
"""
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from utils.logging_config import get_logger

logger = get_logger(__name__)

def count_principal_elements(composition: Any) -> int:
    """
    Count the number of elements in a composition.
    
    Handles various composition formats:
    - Dict: {'Fe': 0.25, 'Ni': 0.25, ...}
    - String: 'Fe0.25Ni0.25Co0.25Mn0.25' or 'Fe,Ni,Co,Mn'
    - List: ['Fe', 'Ni', 'Co', 'Mn']
    
    Args:
        composition: The composition data to parse
        
    Returns:
        Number of elements in the composition
    """
    if isinstance(composition, dict):
        return len([k for k, v in composition.items() if v > 0])
    elif isinstance(composition, str):
        # Try to parse string format
        # Handle formats like "Fe0.25Ni0.25" or "Fe,Ni,Co,Mn"
        if ',' in composition:
            # Comma-separated list
            elements = [e.strip() for e in composition.split(',') if e.strip()]
            return len(elements)
        else:
            # Try to extract element symbols (simplified approach)
            # This is a heuristic and may not be perfect for all formats
            import re
            # Match capital letter followed by optional lowercase letter
            elements = re.findall(r'[A-Z][a-z]?', composition)
            return len(elements)
    elif isinstance(composition, list):
        return len([e for e in composition if e])
    else:
        logger.warning(f"Unknown composition format: {type(composition)}")
        return 0

def filter_hea_samples(
    df: pd.DataFrame,
    min_elements: int = 5,
    bulk_modulus_col: str = 'bulk_modulus',
    composition_col: str = 'composition'
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter HEA samples to retain only those with >= min_elements principal
    elements and valid Bulk Modulus values.
    
    Args:
        df: Input DataFrame with HEA samples
        min_elements: Minimum number of principal elements required (default: 5)
        bulk_modulus_col: Name of the Bulk Modulus column
        composition_col: Name of the composition column
        
    Returns:
        Tuple of (filtered DataFrame, statistics dict)
        
    Raises:
        ValueError: If required columns are missing
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
        
    if bulk_modulus_col not in df.columns:
        raise ValueError(f"Required column '{bulk_modulus_col}' not found in DataFrame")
    if composition_col not in df.columns:
        raise ValueError(f"Required column '{composition_col}' not found in DataFrame")
        
    logger.info(f"Starting filtering: min_elements={min_elements}, bulk_modulus_col={bulk_modulus_col}")
    
    initial_count = len(df)
    logger.info(f"Initial sample count: {initial_count}")
    
    # Count elements for each sample
    logger.info(f"Counting elements in composition column '{composition_col}'...")
    df['_element_count'] = df[composition_col].apply(count_principal_elements)
    
    # Filter for >= min_elements
    element_filter = df['_element_count'] >= min_elements
    element_filtered_count = element_filter.sum()
    logger.info(f"Samples with >= {min_elements} elements: {element_filtered_count}")
    
    # Filter for valid Bulk Modulus (not NaN, not None, and positive if applicable)
    bulk_modulus_filter = df[bulk_modulus_col].notna()
    # Also ensure Bulk Modulus is positive (physical constraint)
    bulk_modulus_positive = df[bulk_modulus_col] > 0
    bulk_modulus_valid = bulk_modulus_filter & bulk_modulus_positive
    
    bulk_filtered_count = bulk_modulus_valid.sum()
    logger.info(f"Samples with valid Bulk Modulus: {bulk_filtered_count}")
    
    # Apply both filters
    combined_filter = element_filter & bulk_modulus_valid
    filtered_df = df[combined_filter].copy()
    
    final_count = len(filtered_df)
    logger.info(f"Final sample count after filtering: {final_count}")
    
    # Calculate statistics
    stats = {
        'initial_count': initial_count,
        'element_filtered_count': element_filtered_count,
        'bulk_modulus_filtered_count': bulk_filtered_count,
        'final_count': final_count,
        'removed_by_element_count': initial_count - element_filtered_count,
        'removed_by_bulk_modulus': initial_count - bulk_filtered_count,
        'removed_by_both': initial_count - final_count
    }
    
    # Log summary
    logger.info("Filtering complete:")
    logger.info(f"  - Removed {stats['removed_by_element_count']} samples due to < {min_elements} elements")
    logger.info(f"  - Removed {stats['removed_by_bulk_modulus']} samples due to invalid Bulk Modulus")
    logger.info(f"  - Total removed: {stats['removed_by_both']}")
    logger.info(f"  - Retention rate: {final_count/initial_count*100:.2f}%")
    
    # Drop the temporary element count column
    filtered_df = filtered_df.drop(columns=['_element_count'])
    
    return filtered_df, stats

def main():
    """
    Main entry point for standalone execution.
    Reads raw data, applies filtering, and saves processed data.
    """
    import argparse
    import json
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Filter HEA samples')
    parser.add_argument('--input', type=str, required=True, help='Input data file (CSV/JSON)')
    parser.add_argument('--output', type=str, required=True, help='Output data file (CSV)')
    parser.add_argument('--min-elements', type=int, default=5, help='Minimum number of principal elements')
    parser.add_argument('--bulk-modulus-col', type=str, default='bulk_modulus', help='Bulk Modulus column name')
    parser.add_argument('--composition-col', type=str, default='composition', help='Composition column name')
    parser.add_argument('--stats-output', type=str, default=None, help='Output file for filtering statistics (JSON)')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    # Load data
    logger.info(f"Loading data from {input_path}")
    if input_path.suffix.lower() == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix.lower() in ['.json', '.js']:
        df = pd.read_json(input_path)
    else:
        logger.error(f"Unsupported input format: {input_path.suffix}")
        sys.exit(1)
        
    logger.info(f"Loaded {len(df)} samples")
    
    # Apply filtering
    filtered_df, stats = filter_hea_samples(
        df,
        min_elements=args.min_elements,
        bulk_modulus_col=args.bulk_modulus_col,
        composition_col=args.composition_col
    )
    
    # Save filtered data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(filtered_df)} filtered samples to {output_path}")
    
    # Save statistics if requested
    if args.stats_output:
        stats_path = Path(args.stats_output)
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved filtering statistics to {stats_path}")
    
    # Print summary
    print("\n=== Filtering Summary ===")
    print(f"Initial samples: {stats['initial_count']}")
    print(f"Samples with >= {args.min_elements} elements: {stats['element_filtered_count']}")
    print(f"Samples with valid Bulk Modulus: {stats['bulk_modulus_filtered_count']}")
    print(f"Final samples: {stats['final_count']}")
    print(f"Retention rate: {stats['final_count']/stats['initial_count']*100:.2f}%")
    print("=========================\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
