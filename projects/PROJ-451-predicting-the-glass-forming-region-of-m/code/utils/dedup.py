"""
Deduplication utilities for alloy composition data.

This module provides functions to normalize chemical formulas to the Hill system
and deduplicate compositions, retaining records from the primary source (Science Advances)
when duplicates exist.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from collections import defaultdict
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_formula(formula: str) -> str:
    """
    Normalize a chemical formula to the Hill system.

    The Hill system orders elements as:
    1. Carbon (C) first (if present)
    2. Hydrogen (H) second (if C is present)
    3. All other elements alphabetically

    For non-organic compounds (no C), all elements are sorted alphabetically.

    Args:
        formula: Chemical formula string (e.g., "C2H5OH", "Fe2O3", "Zr41.2Ti13.8Cu12.5Ni10Be22.5")

    Returns:
        Normalized formula string with elements sorted according to Hill system.
        Elements are kept with their subscripts/coefficients.
    """
    if not formula or not isinstance(formula, str):
        return ""

    # Parse the formula into element-count pairs
    # This regex matches element symbols followed by optional numeric counts
    pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
    matches = re.findall(pattern, formula)

    if not matches:
        # If no matches found, return original (might be malformed)
        logger.warning(f"Could not parse formula: {formula}")
        return formula

    # Group by element, summing coefficients if element appears multiple times
    element_counts: Dict[str, float] = defaultdict(float)
    for element, count_str in matches:
        count = float(count_str) if count_str else 1.0
        element_counts[element] += count

    # Check if this is an organic compound (contains Carbon)
    has_carbon = 'C' in element_counts

    if has_carbon:
        # Hill system for organic: C first, H second, then alphabetical
        sorted_elements = ['C', 'H'] if 'C' in element_counts and 'H' in element_counts else []
        if 'C' in element_counts:
            sorted_elements = ['C']
            if 'H' in element_counts:
                sorted_elements.append('H')
        # Add remaining elements alphabetically
        remaining = sorted([e for e in element_counts.keys() if e not in ['C', 'H']])
        sorted_elements.extend(remaining)
    else:
        # Hill system for inorganic: all elements alphabetically
        sorted_elements = sorted(element_counts.keys())

    # Reconstruct the formula
    normalized_parts = []
    for element in sorted_elements:
        count = element_counts[element]
        # Format count: if it's a whole number, show as int; otherwise keep decimal
        if count == int(count):
            count_str = str(int(count))
        else:
            # Round to reasonable precision to avoid floating point artifacts
            count_str = f"{count:.4f}".rstrip('0').rstrip('.')
        
        # Omit '1' for single atoms
        if count_str == '1':
            normalized_parts.append(element)
        else:
            normalized_parts.append(f"{element}{count_str}")

    return "".join(normalized_parts)

def get_source_priority(source: Optional[str]) -> int:
    """
    Get priority for a data source. Lower number = higher priority.

    Primary source (Science Advances) gets highest priority.
    Secondary sources (Materials Project) get lower priority.

    Args:
        source: Source identifier string (e.g., "Science Advances", "Materials Project")

    Returns:
        Priority integer (lower is better)
    """
    if source is None:
        return 999

    source_lower = source.lower()
    if 'science advances' in source_lower or 'sciadv' in source_lower:
        return 1
    elif 'materials project' in source_lower or 'mp' in source_lower:
        return 2
    else:
        return 3

def deduplicate_compositions(
    df: pd.DataFrame,
    formula_column: str = 'composition',
    source_column: str = 'source',
    output_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Deduplicate compositions by unique chemical formula.

    When duplicates are found, the record from the primary source (Science Advances)
    is retained according to FR-010.

    Args:
        df: Input DataFrame with composition data
        formula_column: Name of column containing chemical formulas
        source_column: Name of column containing source information
        output_path: Optional path to save the deduplicated DataFrame

    Returns:
        Tuple of (deduplicated DataFrame, statistics dictionary)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return df, {'total_input': 0, 'total_output': 0, 'duplicates_removed': 0}

    logger.info(f"Starting deduplication on {len(df)} records")

    # Create a working copy
    df_work = df.copy()

    # Normalize all formulas
    df_work['normalized_formula'] = df_work[formula_column].apply(normalize_formula)

    # Count duplicates before deduplication
    formula_counts = df_work['normalized_formula'].value_counts()
    duplicate_formulas = formula_counts[formula_counts > 1]

    stats = {
        'total_input': len(df_work),
        'unique_formulas_before': len(formula_counts),
        'duplicate_formulas_count': len(duplicate_formulas),
        'duplicates_removed': 0
    }

    if len(duplicate_formulas) == 0:
        logger.info("No duplicates found")
        if output_path:
            df_work.drop(columns=['normalized_formula']).to_csv(output_path, index=False)
        return df_work.drop(columns=['normalized_formula']), stats

    # Sort by source priority to keep highest priority source first
    df_work['source_priority'] = df_work[source_column].apply(get_source_priority)

    # Sort by normalized formula, then by source priority (ascending)
    df_work = df_work.sort_values(
        by=['normalized_formula', 'source_priority'],
        ascending=[True, True]
    )

    # Keep first occurrence of each normalized formula (highest priority source)
    deduplicated = df_work.drop_duplicates(subset=['normalized_formula'], keep='first')

    # Calculate statistics
    stats['duplicates_removed'] = stats['total_input'] - len(deduplicated)
    stats['total_output'] = len(deduplicated)
    stats['unique_formulas_after'] = deduplicated['normalized_formula'].nunique()

    # Log summary
    logger.info(f"Deduplication complete: {stats['duplicates_removed']} duplicates removed")
    logger.info(f"Retained {len(deduplicated)} unique compositions")

    # Drop helper columns before returning
    result_df = deduplicated.drop(columns=['normalized_formula', 'source_priority'])

    # Save to output path if provided
    if output_path:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Deduplicated data saved to {output_path}")

    return result_df, stats

def get_deduplication_stats(
    original_df: pd.DataFrame,
    deduplicated_df: pd.DataFrame,
    formula_column: str = 'composition'
) -> Dict[str, Any]:
    """
    Generate detailed statistics about the deduplication process.

    Args:
        original_df: Original DataFrame before deduplication
        deduplicated_df: DataFrame after deduplication
        formula_column: Name of column containing chemical formulas

    Returns:
        Dictionary with deduplication statistics
    """
    # Normalize formulas for comparison
    original_normalized = original_df[formula_column].apply(normalize_formula)
    dedup_normalized = deduplicated_df[formula_column].apply(normalize_formula)

    # Count unique formulas
    unique_original = original_normalized.nunique()
    unique_dedup = dedup_normalized.nunique()

    # Find which formulas were removed
    original_counts = original_normalized.value_counts()
    dedup_set = set(dedup_normalized)
    removed_formulas = [f for f, count in original_counts.items() if f not in dedup_set]

    stats = {
        'total_original_records': len(original_df),
        'total_dedup_records': len(deduplicated_df),
        'unique_formulas_original': unique_original,
        'unique_formulas_dedup': unique_dedup,
        'records_removed': len(original_df) - len(deduplicated_df),
        'formulas_with_duplicates': (original_counts > 1).sum(),
        'formulas_removed_completely': len(removed_formulas)
    }

    return stats

def main():
    """
    Main function to demonstrate deduplication.
    This is intended to be called by the ingestion pipeline.
    """
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Example usage - this would normally be called from ingest.py
    logger.info("Deduplication module ready. Use deduplicate_compositions() to process data.")
    return True

if __name__ == "__main__":
    main()
