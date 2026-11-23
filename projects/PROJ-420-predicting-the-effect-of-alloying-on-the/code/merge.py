"""Merge and deduplicate alloy data from multiple sources."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

# Import constants
from constants import YOUNG_MODULUS_TOLERANCE, COMPOSITION_TOLERANCE

# Import logging utilities
from logging_config import get_logger, log_operation

logger = get_logger(__name__)


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from a file.

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

    # Handle cases where data might be wrapped in a key
    if isinstance(data, dict):
        # Try common keys that might contain the list
        for key in ['data', 'results', 'records', 'alloys', 'elastic_data']:
            if key in data and isinstance(data[key], list):
                return data[key]
        # If no common key found, assume the dict itself is the record or return empty
        if not data:
            return []
        # If it's a single record, wrap it
        if not any(isinstance(v, list) for v in data.values()):
            return [data]
        # Fallback: return first list found
        for v in data.values():
            if isinstance(v, list):
                return v
        return []
    elif isinstance(data, list):
        return data
    else:
        logger.warning(f"Unexpected JSON structure in {file_path}: {type(data)}")
        return []


def normalize_composition(composition: Dict[str, float]) -> Dict[str, float]:
    """Normalize composition to atomic fractions and round for comparison.

    Args:
        composition: Dictionary of element -> fraction (wt% or at%).

    Returns:
        Dictionary of element -> normalized atomic fraction (rounded).
    """
    # Sum all values to determine if we need normalization
    total = sum(composition.values())
    if total == 0:
        return composition

    # Normalize to sum to 1.0
    normalized = {k: v / total for k, v in composition.items()}

    # Round to handle floating point precision issues
    rounded = {k: round(v, 6) for k, v in normalized.items()}

    return rounded


def get_atomic_fraction_sum(composition: Dict[str, float], elements: List[str]) -> float:
    """Calculate the sum of atomic fractions for specific elements.

    Args:
        composition: Normalized atomic fractions.
        elements: List of element symbols to sum.

    Returns:
        Sum of atomic fractions for the specified elements.
    """
    return sum(composition.get(e, 0.0) for e in elements)


def normalize_composition_row(row: pd.Series, major_elements: List[str] = None) -> pd.Series:
    """Normalize the composition column in a DataFrame row.

    Args:
        row: DataFrame row.
        major_elements: List of major element symbols. If None, uses all keys in composition.

    Returns:
        Row with normalized composition.
    """
    if 'composition' not in row or row['composition'] is None:
        return row

    comp = row['composition']
    if isinstance(comp, str):
        try:
            comp = json.loads(comp)
        except json.JSONDecodeError:
            return row

    if not isinstance(comp, dict):
        return row

    # Determine elements to normalize
    if major_elements:
        elements_to_normalize = [e for e in major_elements if e in comp]
        if not elements_to_normalize:
            return row
    else:
        elements_to_normalize = list(comp.keys())

    # Normalize
    total = sum(comp.get(e, 0) for e in elements_to_normalize)
    if total == 0:
        return row

    new_comp = comp.copy()
    for e in elements_to_normalize:
        new_comp[e] = comp[e] / total

    row['composition'] = new_comp
    return row


def are_compositions_equal(comp1: Dict[str, float], comp2: Dict[str, float], tolerance: float = COMPOSITION_TOLERANCE) -> bool:
    """Check if two compositions are equal within tolerance.

    Args:
        comp1: First composition dict.
        comp2: Second composition dict.
        tolerance: Tolerance for comparison.

    Returns:
        True if compositions are equal within tolerance.
    """
    # Get all unique elements
    all_elements = set(comp1.keys()) | set(comp2.keys())

    for elem in all_elements:
        val1 = comp1.get(elem, 0.0)
        val2 = comp2.get(elem, 0.0)

        if abs(val1 - val2) > tolerance:
            return False

    return True


def prefer_measurement_method(method1: Optional[str], method2: Optional[str]) -> bool:
    """Determine if method1 is preferred over method2 based on measurement method.

    Priority: 'Ultrasonic' or 'Direct' > others.

    Args:
        method1: First measurement method string.
        method2: Second measurement method string.

    Returns:
        True if method1 is preferred, False otherwise.
    """
    preferred_keywords = ['ultrasonic', 'direct']

    def is_preferred(method: Optional[str]) -> bool:
        if not method:
            return False
        method_lower = method.lower()
        return any(keyword in method_lower for keyword in preferred_keywords)

    pref1 = is_preferred(method1)
    pref2 = is_preferred(method2)

    if pref1 and not pref2:
        return True
    if pref2 and not pref1:
        return False
    # Both preferred or both not preferred - defer to Young's Modulus
    return False


def merge_and_deduplicate(mp_data: List[Dict], nist_data: List[Dict]) -> pd.DataFrame:
    """Merge data from Materials Project and NIST, deduplicating based on composition and Young's Modulus.

    Args:
        mp_data: List of records from Materials Project.
        nist_data: List of records from NIST.

    Returns:
        Deduplicated DataFrame.
    """
    # Combine data with source tracking
    all_records = []

    for record in mp_data:
        new_record = record.copy()
        new_record['source'] = 'Materials Project'
        new_record['measurement_method'] = new_record.get('measurement_method') or new_record.get('method')
        all_records.append(new_record)

    for record in nist_data:
        new_record = record.copy()
        new_record['source'] = 'NIST MDR'
        new_record['measurement_method'] = new_record.get('measurement_method') or new_record.get('method')
        all_records.append(new_record)

    if not all_records:
        logger.warning("No records to merge.")
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Ensure required fields exist
    required_fields = ['poisson_ratio', 'young_modulus', 'composition']
    for field in required_fields:
        if field not in df.columns:
            logger.warning(f"Required field '{field}' missing from data. Creating empty column.")
            df[field] = None

    # Normalize compositions
    df['normalized_composition'] = df['composition'].apply(normalize_composition)

    # Group by normalized composition and Young's Modulus (within tolerance)
    # We'll use a simple approach: iterate and compare
    unique_records = []
    used_indices = set()

    for i, row_i in df.iterrows():
        if i in used_indices:
            continue

        # Find all matching records
        matches = [i]
        for j, row_j in df.iterrows():
            if j == i or j in used_indices:
                continue

            # Check Young's Modulus tolerance
            ym_i = row_i.get('young_modulus')
            ym_j = row_j.get('young_modulus')

            if ym_i is None or ym_j is None:
                continue

            if abs(float(ym_i) - float(ym_j)) > YOUNG_MODULUS_TOLERANCE:
                continue

            # Check composition equality
            if are_compositions_equal(row_i['normalized_composition'], row_j['normalized_composition']):
                matches.append(j)

        # Resolve conflict among matches
        best_idx = matches[0]
        best_row = df.iloc[best_idx]

        for match_idx in matches[1:]:
            match_row = df.iloc[match_idx]

            # Compare measurement methods
            pref_method = prefer_measurement_method(
                best_row.get('measurement_method'),
                match_row.get('measurement_method')
            )

            if pref_method:
                continue

            # If methods are equal preference, check Young's Modulus (higher is better)
            if not pref_method:
                best_ym = float(best_row.get('young_modulus') or 0)
                match_ym = float(match_row.get('young_modulus') or 0)

                if match_ym > best_ym:
                    best_idx = match_idx
                    best_row = match_row

        # Add best record
        unique_records.append(df.iloc[best_idx])
        used_indices.update(matches)

    # Create final DataFrame
    result_df = pd.DataFrame(unique_records)

    # Clean up temporary column
    if 'normalized_composition' in result_df.columns:
        result_df = result_df.drop(columns=['normalized_composition'])

    # Ensure numeric types
    if 'poisson_ratio' in result_df.columns:
        result_df['poisson_ratio'] = pd.to_numeric(result_df['poisson_ratio'], errors='coerce')
    if 'young_modulus' in result_df.columns:
        result_df['young_modulus'] = pd.to_numeric(result_df['young_modulus'], errors='coerce')

    return result_df


def main():
    """Main entry point for the merge script."""
    log_operation("merge_start", module="merge")

    # Define paths
    base_dir = Path(__file__).parent.parent
    mp_path = base_dir / "data" / "raw" / "mp_alloys.json"
    nist_path = base_dir / "data" / "raw" / "nist_alloys.json"
    output_path = base_dir / "data" / "processed" / "merged_raw.parquet"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check input files
    if not mp_path.exists():
        raise FileNotFoundError(f"Materials Project data file not found: {mp_path}")
    if not nist_path.exists():
        raise FileNotFoundError(f"NIST data file not found: {nist_path}")

    logger.info(f"Loading data from {mp_path} and {nist_path}")

    # Load data
    try:
        mp_data = load_json_file(str(mp_path))
        nist_data = load_json_file(str(nist_path))
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    logger.info(f"Loaded {len(mp_data)} records from Materials Project")
    logger.info(f"Loaded {len(nist_data)} records from NIST")

    # Merge and deduplicate
    logger.info("Merging and deduplicating data...")
    merged_df = merge_and_deduplicate(mp_data, nist_data)

    logger.info(f"Merged dataset contains {len(merged_df)} unique records")

    # Save to parquet
    logger.info(f"Saving merged data to {output_path}")
    merged_df.to_parquet(str(output_path), index=False)

    log_operation("merge_complete", records=len(merged_df), output=str(output_path))

    print(f"Successfully merged {len(merged_df)} records to {output_path}")
    return merged_df


if __name__ == "__main__":
    main()