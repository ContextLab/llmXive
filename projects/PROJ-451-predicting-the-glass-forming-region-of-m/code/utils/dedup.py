"""
Deduplication utilities for alloy composition data.

This module provides functions to normalize chemical formulas and deduplicate
compositions based on unique chemical formulas with normalized atomic fractions.
It follows the principle of unique chemical identity as defined in Wikidata Q19881044.
"""
from typing import Dict, List, Any, Optional, Tuple
import re
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def normalize_formula(formula: str) -> str:
    """
    Normalize a chemical formula to a canonical representation.
    
    This function:
    1. Removes whitespace
    2. Sorts elements alphabetically (Hill system variation for alloys)
    3. Normalizes atomic fractions to a common denominator
    4. Returns a string representation of the normalized composition
    
    Args:
        formula: Input chemical formula string (e.g., "Zr50Cu40Al10")
    
    Returns:
        Normalized formula string
    """
    if not formula or not isinstance(formula, str):
        raise ValueError(f"Invalid formula input: {formula}")
    
    # Clean the formula
    formula = formula.strip().replace(" ", "")
    
    # Parse elements and their counts/fractions
    # Handle both integer counts (Zr50Cu40Al10) and fractional (Zr0.5Cu0.4Al0.1)
    elements = {}
    
    # Pattern to match element symbols and their counts
    # Element symbols: Capital letter followed by optional lowercase
    # Count: Integer or float
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*|\d*\.?\d+)'
    matches = re.findall(pattern, formula)
    
    if not matches:
        # Try to handle formulas without explicit counts (assume equal parts)
        # This is a fallback for simple cases like "ZrCu"
        simple_pattern = r'([A-Z][a-z]?)'
        simple_matches = re.findall(simple_pattern, formula)
        if simple_matches:
            count = 1.0 / len(simple_matches)
            for elem in simple_matches:
                elements[elem] = count
            # Normalize and return
            return _normalize_elements_dict(elements)
        else:
            raise ValueError(f"Could not parse formula: {formula}")
    
    total = 0.0
    for elem, count_str in matches:
        try:
            count = float(count_str)
            elements[elem] = count
            total += count
        except ValueError:
            raise ValueError(f"Invalid count '{count_str}' for element '{elem}' in formula '{formula}'")
    
    if total == 0:
        raise ValueError(f"Total composition is zero for formula: {formula}")
    
    # Normalize to sum to 1.0 (atomic fractions)
    for elem in elements:
        elements[elem] /= total
    
    return _normalize_elements_dict(elements)


def _normalize_elements_dict(elements: Dict[str, float]) -> str:
    """
    Convert a dictionary of elements to a normalized formula string.
    
    Args:
        elements: Dictionary mapping element symbols to normalized fractions
    
    Returns:
        Normalized formula string (sorted alphabetically)
    """
    # Sort elements alphabetically (Hill system for alloys)
    sorted_elements = sorted(elements.items(), key=lambda x: x[0])
    
    # Build the formula string with normalized fractions (rounded to 3 decimals)
    parts = []
    for elem, fraction in sorted_elements:
        # Round to avoid floating point precision issues
        rounded_frac = round(fraction, 3)
        if rounded_frac > 0:
            parts.append(f"{elem}{rounded_frac:.3f}")
    
    return "".join(parts)


def get_source_priority(source: Optional[str]) -> int:
    """
    Get the priority level for a data source.
    
    Higher priority sources are kept when duplicates are found.
    
    Priority order:
    1. Materials Project (highest)
    2. Zenodo (Science Advances dataset)
    3. Synthetic (fallback)
    4. Unknown/Other (lowest)
    
    Args:
        source: Source identifier string
    
    Returns:
        Priority integer (higher is better)
    """
    source = source.lower() if source else ""
    
    if "materials project" in source or "mp-" in source:
        return 3
    elif "zenodo" in source or "science advances" in source:
        return 2
    elif "synthetic" in source:
        return 1
    else:
        return 0


def deduplicate_compositions(
    compositions: List[Dict[str, Any]],
    formula_key: str = "composition",
    source_key: str = "source"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Deduplicate a list of composition records by normalized chemical formula.
    
    When duplicates are found, the record from the highest priority source is kept.
    If sources have equal priority, the first occurrence is retained.
    
    Args:
        compositions: List of composition dictionaries
        formula_key: Key name for the composition formula in each record
        source_key: Key name for the source identifier in each record
    
    Returns:
        Tuple of (deduplicated_list, stats_dict)
        stats_dict contains:
            - total_input: Total number of input records
            - total_output: Total number of output records
            - duplicates_removed: Number of duplicates removed
            - duplicate_groups: Number of groups with duplicates
    """
    if not compositions:
        logger.warning("Empty composition list provided to deduplicate_compositions")
        return [], {
            "total_input": 0,
            "total_output": 0,
            "duplicates_removed": 0,
            "duplicate_groups": 0
        }
    
    # Group by normalized formula
    formula_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    for idx, record in enumerate(compositions):
        if formula_key not in record:
            logger.warning(f"Record {idx} missing formula key '{formula_key}', skipping")
            continue
        
        try:
            formula = record[formula_key]
            normalized = normalize_formula(formula)
            formula_groups[normalized].append(record)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize formula '{record.get(formula_key, 'N/A')}': {e}")
            # Keep original record with a flag
            record["_dedup_error"] = str(e)
            formula_groups[f"__error_{idx}__"].append(record)
    
    # Select best record from each group
    deduplicated = []
    duplicate_groups = 0
    duplicates_removed = 0
    
    for normalized_formula, group in formula_groups.items():
        if len(group) > 1:
            duplicate_groups += 1
            duplicates_removed += len(group) - 1
            
            # Sort by source priority (descending) then by original order
            def sort_key(record):
                source = record.get(source_key, "")
                return -get_source_priority(source)
            
            group.sort(key=sort_key)
            best_record = group[0]
            
            # Add metadata about duplicates
            if "_duplicate_sources" not in best_record:
                best_record["_duplicate_sources"] = []
            best_record["_duplicate_sources"].extend([
                r.get(source_key, "unknown") for r in group[1:]
            ])
            best_record["_duplicate_count"] = len(group) - 1
        else:
            best_record = group[0]
        
        deduplicated.append(best_record)
    
    stats = {
        "total_input": len(compositions),
        "total_output": len(deduplicated),
        "duplicates_removed": duplicates_removed,
        "duplicate_groups": duplicate_groups
    }
    
    logger.info(f"Deduplication complete: {stats['duplicates_removed']} duplicates removed "
               f"from {stats['duplicate_groups']} groups. "
               f"Kept {stats['total_output']} unique compositions.")
    
    return deduplicated, stats


def get_deduplication_stats(
    original_count: int,
    deduplicated_count: int
) -> Dict[str, float]:
    """
    Calculate deduplication statistics.
    
    Args:
        original_count: Number of records before deduplication
        deduplicated_count: Number of records after deduplication
    
    Returns:
        Dictionary with statistics:
            - original_count
            - deduplicated_count
            - duplicates_removed
            - duplicate_percentage
            - retention_rate
    """
    duplicates_removed = original_count - deduplicated_count
    duplicate_percentage = (duplicates_removed / original_count * 100) if original_count > 0 else 0.0
    retention_rate = (deduplicated_count / original_count * 100) if original_count > 0 else 0.0
    
    return {
        "original_count": original_count,
        "deduplicated_count": deduplicated_count,
        "duplicates_removed": duplicates_removed,
        "duplicate_percentage": round(duplicate_percentage, 2),
        "retention_rate": round(retention_rate, 2)
    }
