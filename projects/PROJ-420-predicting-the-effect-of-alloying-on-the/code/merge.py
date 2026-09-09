"""
Merge and deduplicate data from Materials Project and NIST sources.

Implements the logic for T009c:
- Merge data from data/raw/mp_alloys.json and data/raw/nist_alloys.json.
- Deduplicate based on normalized atomic fractions and Young's Modulus within tolerance.
- Conflict resolution: Prefer 'Ultrasonic' or 'Direct' measurement methods, then higher Young's Modulus.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Import config for paths and constants
# Note: We use a relative import approach that works when run as a module or script
# The API surface shows 'from config import get_config' is used elsewhere
try:
    from config import get_config
except ImportError:
    # Fallback for direct execution in some environments
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config

from logging_config import get_logger, setup_logging

# Setup logger
logger = setup_logging(level="INFO")
logger.info("Starting merge and deduplication process")

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # If it's a dict, wrap it in a list
        if isinstance(data, dict):
            data = [data]
        else:
            raise ValueError(f"Unexpected JSON structure in {file_path}: expected list or dict")
    
    return data

def normalize_composition(composition: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize atomic fractions to sum to 1.0.
    Handles cases where the sum might be slightly off due to floating point errors.
    """
    total = sum(composition.values())
    if total == 0:
        return composition
    
    return {k: v / total for k, v in composition.items()}

def get_atomic_fraction_sum(row: pd.Series, elements: List[str]) -> float:
    """Calculate the sum of atomic fractions for specified elements."""
    total = 0.0
    for elem in elements:
        total += row.get(elem, 0.0)
    return total

def normalize_composition_row(row: pd.Series, elements: List[str]) -> Dict[str, float]:
    """
    Create a normalized composition dictionary for a row.
    Only includes the specified elements, normalized to sum to 1.0.
    """
    raw_comp = {elem: row.get(elem, 0.0) for elem in elements}
    return normalize_composition(raw_comp)

def are_compositions_equal(comp1: Dict[str, float], comp2: Dict[str, float], tolerance: float = 1e-6) -> bool:
    """
    Check if two normalized compositions are equal within a tolerance.
    Compares all elements present in either composition.
    """
    all_elements = set(comp1.keys()) | set(comp2.keys())
    
    for elem in all_elements:
        val1 = comp1.get(elem, 0.0)
        val2 = comp2.get(elem, 0.0)
        
        if abs(val1 - val2) > tolerance:
            return False
    
    return True

def prefer_measurement_method(method1: Optional[str], method2: Optional[str]) -> bool:
    """
    Determine if method1 is preferred over method2 based on measurement method.
    Returns True if method1 should be kept, False if method2 should be kept.
    """
    # If either is None, treat as empty string
    m1 = (method1 or "").lower()
    m2 = (method2 or "").lower()
    
    # Check for preferred methods
    preferred_keywords = ['ultrasonic', 'direct']
    
    m1_preferred = any(keyword in m1 for keyword in preferred_keywords)
    m2_preferred = any(keyword in m2 for keyword in preferred_keywords)
    
    if m1_preferred and not m2_preferred:
        return True
    if not m1_preferred and m2_preferred:
        return False
    
    # If both or neither are preferred, return False (will use Young's Modulus tiebreaker)
    return False

def merge_and_deduplicate(mp_data: List[Dict], nist_data: List[Dict], tolerance: float = 1e-6) -> pd.DataFrame:
    """
    Merge and deduplicate data from Materials Project and NIST sources.
    
    Args:
        mp_data: List of dictionaries from Materials Project
        nist_data: List of dictionaries from NIST
        tolerance: Numerical tolerance for comparing Young's Modulus and compositions
    
    Returns:
        Deduplicated DataFrame
    """
    # Convert to DataFrames
    df_mp = pd.DataFrame(mp_data)
    df_nist = pd.DataFrame(nist_data)
    
    logger.info(f"Loaded {len(df_mp)} records from Materials Project")
    logger.info(f"Loaded {len(df_nist)} records from NIST")
    
    # Add source column
    df_mp['source'] = 'MaterialsProject'
    df_nist['source'] = 'NIST'
    
    # Concatenate
    combined_df = pd.concat([df_mp, df_nist], ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} records before deduplication")
    
    # Define elements to consider for composition matching
    elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    # Normalize compositions and create a key for grouping
    def create_composition_key(row):
        comp = normalize_composition_row(row, elements)
        # Create a string key from sorted elements and their values
        # Round to avoid floating point issues in string representation
        parts = [f"{elem}:{comp.get(elem, 0.0):.6f}" for elem in sorted(elements)]
        return "|".join(parts)
    
    # Create composition key
    combined_df['composition_key'] = combined_df.apply(create_composition_key, axis=1)
    
    # Create Young's Modulus rounded key for grouping (within tolerance)
    # We'll group by rounded YM values and then check exact matches within groups
    ym_tolerance = tolerance * 100  # Slightly larger tolerance for YM grouping
    combined_df['ym_key'] = (combined_df['young_modulus'] / ym_tolerance).round() * ym_tolerance
    
    # Group by composition_key and ym_key to find potential duplicates
    groups = combined_df.groupby(['composition_key', 'ym_key'])
    
    deduplicated_records = []
    duplicate_count = 0
    
    for (comp_key, ym_key), group in groups:
        if len(group) == 1:
            # No duplicates in this group
            record = group.iloc[0].to_dict()
            deduplicated_records.append(record)
        else:
            # Multiple records with same composition and similar YM
            duplicate_count += len(group) - 1
            
            # Apply conflict resolution
            # 1. Prefer records with 'Ultrasonic' or 'Direct' measurement method
            preferred_records = []
            other_records = []
            
            for _, row in group.iterrows():
                method = row.get('measurement_method', '')
                if prefer_measurement_method(method, None):  # Compare against "no preference"
                    preferred_records.append(row)
                else:
                    other_records.append(row)
            
            # If we have preferred records, use them; otherwise use all
            candidates = preferred_records if preferred_records else other_records
            
            # If still multiple, prefer higher Young's Modulus
            if len(candidates) > 1:
                best_record = max(candidates, key=lambda x: x.get('young_modulus', 0))
            else:
                best_record = candidates[0]
            
            deduplicated_records.append(best_record.to_dict())
    
    deduplicated_df = pd.DataFrame(deduplicated_records)
    logger.info(f"After deduplication: {len(deduplicated_df)} records (removed {duplicate_count} duplicates)")
    
    # Drop temporary columns
    deduplicated_df = deduplicated_df.drop(columns=['composition_key', 'ym_key'], errors='ignore')
    
    return deduplicated_df

def main():
    """Main entry point for the merge and deduplication process."""
    config = get_config()
    
    # Define paths
    mp_file = config.data_raw / 'mp_alloys.json'
    nist_file = config.data_raw / 'nist_alloys.json'
    output_file = config.data_processed / 'alloys_merged.parquet'
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading data from {mp_file} and {nist_file}")
        mp_data = load_json_file(mp_file)
        nist_data = load_json_file(nist_file)
        
        # Get tolerance from config or use default
        tolerance = getattr(config, 'composition_tolerance', 1e-6)
        
        # Merge and deduplicate
        merged_df = merge_and_deduplicate(mp_data, nist_data, tolerance)
        
        # Save to parquet
        merged_df.to_parquet(output_file, index=False)
        logger.info(f"Saved merged dataset to {output_file}")
        
        # Log summary
        logger.info(f"Final dataset shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
        return merged_df
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during merge and deduplication: {e}")
        raise

if __name__ == '__main__':
    main()