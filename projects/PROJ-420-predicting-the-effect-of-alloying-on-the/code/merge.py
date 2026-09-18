"""Merge and deduplicate raw data from multiple sources."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Import constants for tolerances
try:
    from constants import YOUNG_MODULUS_TOLERANCE, COMPOSITION_TOLERANCE
except ImportError:
    # Fallback for when running as script directly
    YOUNG_MODULUS_TOLERANCE = 0.1
    COMPOSITION_TOLERANCE = 0.001

logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of records from the JSON file.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle case where data is wrapped in a key
    if isinstance(data, dict):
        # Try common keys
        for key in ['data', 'results', 'records', 'alloys', 'elastic_data']:
            if key in data and isinstance(data[key], list):
                return data[key]
        # If no known key found, return the dict values if they are lists
        for value in data.values():
            if isinstance(value, list):
                return value
        # Return as single-item list if it's a dict
        return [data]

    if isinstance(data, list):
        return data

    raise ValueError(f"Unexpected data format in {file_path}: expected list or dict")


def normalize_composition(composition: Dict[str, float]) -> Dict[str, float]:
    """Normalize composition to atomic fractions.

    Args:
        composition: Dictionary of element: fraction (either wt% or at%).

    Returns:
        Normalized atomic fractions.
    """
    if not composition:
        return {}

    # Check if values sum to ~100 (wt%) or ~1.0 (at%)
    total = sum(composition.values())

    if total > 10.0:  # Likely wt%
        # Convert wt% to at%
        from periodictable import elements
        at_fractions = {}
        for element, weight_pct in composition.items():
            element_name = element.strip().title()
            try:
                elem = getattr(elements, element_name)
                atomic_weight = elem.mass
                at_fractions[element] = weight_pct / atomic_weight
            except (AttributeError, KeyError):
                # If element not found, keep as is (might be custom notation)
                at_fractions[element] = weight_pct

        # Normalize to sum to 1.0
        total_at = sum(at_fractions.values())
        if total_at > 0:
            at_fractions = {k: v / total_at for k, v in at_fractions.items()}
        return at_fractions
    else:
        # Already at% or normalized
        if total > 0 and abs(total - 1.0) > 0.01:
            # Normalize anyway
            return {k: v / total for k, v in composition.items()}
        return composition


def get_atomic_fraction_sum(composition: Dict[str, float], elements: List[str]) -> float:
    """Calculate the sum of atomic fractions for specified elements.

    Args:
        composition: Dictionary of element: atomic_fraction.
        elements: List of element symbols to sum.

    Returns:
        Sum of atomic fractions for the specified elements.
    """
    return sum(composition.get(elem, 0.0) for elem in elements)


def normalize_composition_row(row: pd.Series, element_columns: List[str]) -> Dict[str, float]:
    """Normalize a single row's composition to atomic fractions.

    Args:
        row: DataFrame row.
        element_columns: List of column names for elements.

    Returns:
        Dictionary of element: normalized_fraction.
    """
    composition = {}
    for elem in element_columns:
        if elem in row.index and pd.notna(row[elem]):
            composition[elem] = float(row[elem])

    return normalize_composition(composition)


def are_compositions_equal(comp1: Dict[str, float], comp2: Dict[str, float],
                           tolerance: float = COMPOSITION_TOLERANCE) -> bool:
    """Check if two compositions are equal within tolerance.

    Args:
        comp1: First composition dictionary.
        comp2: Second composition dictionary.
        tolerance: Maximum allowed difference for each element.

    Returns:
        True if compositions are considered equal.
    """
    all_elements = set(comp1.keys()) | set(comp2.keys())

    for elem in all_elements:
        val1 = comp1.get(elem, 0.0)
        val2 = comp2.get(elem, 0.0)
        if abs(val1 - val2) > tolerance:
            return False

    return True


def prefer_measurement_method(method1: Optional[str], method2: Optional[str]) -> int:
    """Determine which measurement method is preferred.

    Priority: Ultrasonic > Direct > others.

    Args:
        method1: First measurement method string.
        method2: Second measurement method string.

    Returns:
        1 if method1 is preferred, -1 if method2 is preferred, 0 if equal.
    """
    def get_priority(method: Optional[str]) -> int:
        if not method:
            return 0
        method_lower = method.lower()
        if 'ultrasonic' in method_lower:
            return 2
        if 'direct' in method_lower:
            return 1
        return 0

    p1 = get_priority(method1)
    p2 = get_priority(method2)

    if p1 > p2:
        return 1
    elif p2 > p1:
        return -1
    else:
        return 0


def merge_and_deduplicate(mp_data: List[Dict[str, Any]], nist_data: List[Dict[str, Any]],
                          output_path: str) -> pd.DataFrame:
    """Merge and deduplicate data from Materials Project and NIST.

    Deduplication Logic:
    - Merge on exact match of normalized atomic fractions and Young's Modulus within tolerance.
    - Conflict Resolution: Prefer 'Ultrasonic' or 'Direct' methods; if tie, prefer higher Young's Modulus.

    Args:
        mp_data: List of records from Materials Project.
        nist_data: List of records from NIST.
        output_path: Path to save the merged parquet file.

    Returns:
        Merged and deduplicated DataFrame.
    """
    logger.info(f"Merging {len(mp_data)} MP records and {len(nist_data)} NIST records")

    # Convert to DataFrames
    mp_df = pd.DataFrame(mp_data) if mp_data else pd.DataFrame()
    nist_df = pd.DataFrame(nist_data) if nist_data else pd.DataFrame()

    if mp_df.empty and nist_df.empty:
        raise ValueError("No data to merge from either source")

    # Standardize column names
    def standardize_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
        if df.empty:
            return df

        # Map common variations to standard names
        column_mappings = {
            'poisson_ratio': ['poisson_ratio', 'poissons_ratio', 'poisson', 'pr'],
            'young_modulus': ['young_modulus', 'youngs_modulus', 'young_mod', 'ym', 'e_modulus'],
            'measurement_method': ['measurement_method', 'method', 'measurement_type', 'technique'],
            'composition': ['composition', 'elements', 'chemical_composition', 'alloy_composition']
        }

        for std_name, variations in column_mappings.items():
            for var in variations:
                if var in df.columns:
                    if std_name not in df.columns:
                        df[std_name] = df[var]
                    # Drop the old column if it's different
                    if var != std_name:
                        df = df.drop(columns=[var])

        # Ensure composition is a dict if it's a string
        if 'composition' in df.columns:
            def parse_composition(val):
                if isinstance(val, dict):
                    return val
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except json.JSONDecodeError:
                        # Try to parse simple format "Cu:0.1, Mg:0.2"
                        result = {}
                        parts = val.replace(',', ' ').split()
                        for i in range(0, len(parts), 2):
                            if i + 1 < len(parts):
                                elem = parts[i].rstrip(':')
                                try:
                                    result[elem] = float(parts[i+1].lstrip(':'))
                                except ValueError:
                                    pass
                        return result
                return {}

            df['composition'] = df['composition'].apply(parse_composition)

        # Add source column
        df['source'] = source

        return df

    mp_df = standardize_columns(mp_df, 'Materials Project')
    nist_df = standardize_columns(nist_df, 'NIST MDR')

    # Combine
    combined_df = pd.concat([mp_df, nist_df], ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} records")

    # Normalize compositions and prepare for merging
    element_columns = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    combined_df['normalized_composition'] = combined_df['composition'].apply(
        lambda x: normalize_composition(x)
    )

    # Create a hashable representation of composition for grouping
    def comp_to_tuple(comp: Dict[str, float]) -> tuple:
        return tuple(sorted([(k, round(v, 6)) for k, v in comp.items()]))

    combined_df['comp_key'] = combined_df['normalized_composition'].apply(comp_to_tuple)

    # Group by Young's Modulus (binned) and composition
    # First, bin Young's Modulus
    if 'young_modulus' in combined_df.columns:
        ym_tolerance = YOUNG_MODULUS_TOLERANCE
        combined_df['ym_bin'] = combined_df['young_modulus'].apply(
            lambda x: round(x / ym_tolerance) * ym_tolerance if pd.notna(x) else None
        )
    else:
        combined_df['ym_bin'] = None

    # Group by composition key and ym_bin
    groups = combined_df.groupby(['comp_key', 'ym_bin'])

    deduplicated_records = []
    duplicate_count = 0

    for (comp_key, ym_bin), group in groups:
        if len(group) == 1:
            deduplicated_records.append(group.iloc[0])
        else:
            duplicate_count += len(group) - 1
            # Apply conflict resolution
            # Prefer Ultrasonic or Direct
            methods = group['measurement_method'].tolist()
            priorities = [prefer_measurement_method(methods[0], m) for m in methods[1:]]

            if 1 in priorities:
                # First one is preferred
                best_idx = group.index[0]
            elif -1 in priorities:
                # Another one is preferred
                best_idx = group.index[priorities.index(-1) + 1]
            else:
                # Tie: prefer higher Young's Modulus
                ym_values = group['young_modulus'].fillna(-1)
                best_idx = ym_values.idxmax()

            deduplicated_records.append(group.loc[best_idx])

    result_df = pd.DataFrame(deduplicated_records)

    # Clean up temporary columns
    temp_cols = ['normalized_composition', 'comp_key', 'ym_bin']
    result_df = result_df.drop(columns=[c for c in temp_cols if c in result_df.columns])

    logger.info(f"Removed {duplicate_count} duplicate records")
    logger.info(f"Final merged dataset has {len(result_df)} unique records")

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    result_df.to_parquet(output_path, index=False)
    logger.info(f"Merged data saved to {output_path}")

    return result_df


def main():
    """Main entry point for merging raw data."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    base_dir = Path(__file__).parent.parent
    mp_path = base_dir / 'data' / 'raw' / 'mp_alloys.json'
    nist_path = base_dir / 'data' / 'raw' / 'nist_alloys.json'
    output_path = base_dir / 'data' / 'processed' / 'merged_raw.parquet'

    # Check for input files
    if not mp_path.exists():
        logger.error(f"Materials Project data not found: {mp_path}")
        logger.error("Run T009a first to download MP data")
        sys.exit(1)

    if not nist_path.exists():
        logger.error(f"NIST data not found: {nist_path}")
        logger.error("Run T009b first to download NIST data")
        sys.exit(1)

    try:
        # Load data
        mp_data = load_json_file(str(mp_path))
        nist_data = load_json_file(str(nist_path))

        if not mp_data:
            raise ValueError("No data loaded from Materials Project")
        if not nist_data:
            raise ValueError("No data loaded from NIST")

        logger.info(f"Loaded {len(mp_data)} MP records and {len(nist_data)} NIST records")

        # Merge and deduplicate
        result_df = merge_and_deduplicate(mp_data, nist_data, str(output_path))

        # Verify output
        if result_df.empty:
            raise ValueError("Merged dataset is empty")

        logger.info(f"Successfully merged data. Output: {output_path}")
        logger.info(f"Columns: {list(result_df.columns)}")
        logger.info(f"Sample record:\n{result_df.iloc[0].to_dict()}")

    except Exception as e:
        logger.error(f"Error during merge: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
