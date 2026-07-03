"""
Utility module for deduplicating alloy compositions.

This module provides functions to normalize chemical formulas,
deduplicate compositions based on unique chemical formulas,
and retain the primary source (Science Advances) when duplicates exist.
"""
from typing import Dict, List, Any, Optional
import re
from collections import defaultdict

# Source priority: Science Advances is the primary source
SOURCE_PRIORITY = {
    "Science Advances": 0,
    "Materials Project": 1,
    "Zenodo": 1,
    "default": 2
}

def normalize_formula(formula: str) -> str:
    """
    Normalize a chemical formula to a canonical representation.
    
    This function:
    1. Removes whitespace
    2. Sorts elements alphabetically
    3. Normalizes atomic fractions to a common denominator
    4. Returns a string representation of the normalized formula
    
    Args:
        formula: Chemical formula string (e.g., "Fe2Ni3", "Fe0.4Ni0.6")
        
    Returns:
        Normalized formula string with elements sorted alphabetically
    """
    if not formula or not isinstance(formula, str):
        return ""
    
    # Remove whitespace and convert to uppercase
    formula = formula.strip().upper()
    
    # Parse elements and their counts
    # Handle both integer and fractional notation
    element_pattern = re.compile(r'([A-Z][a-z]*)(\d*\.?\d*)')
    elements = {}
    
    matches = element_pattern.findall(formula)
    
    if not matches:
        # Try to handle simple element symbols without counts
        simple_pattern = re.compile(r'([A-Z][a-z]*)')
        simple_matches = simple_pattern.findall(formula)
        for elem in simple_matches:
            elements[elem] = 1
    else:
        for elem, count_str in matches:
            if count_str == '' or count_str == '.':
                count = 1.0
            else:
                try:
                    count = float(count_str)
                except ValueError:
                    count = 1.0
            elements[elem] = count
    
    if not elements:
        return formula
    
    # Find the greatest common divisor for integer normalization
    # First, convert to fractions to handle decimals
    from fractions import Fraction
    
    fractions = {}
    for elem, count in elements.items():
        fractions[elem] = Fraction(count).limit_denominator(1000)
    
    # Find common denominator
    common_denom = 1
    for frac in fractions.values():
        common_denom = common_denom * frac.denominator // re.gcd(common_denom, frac.denominator)
    
    # Scale to integers
    scaled = {}
    for elem, frac in fractions.items():
        scaled[elem] = int(frac * common_denom)
    
    # Sort elements alphabetically and build normalized string
    sorted_elements = sorted(scaled.items())
    normalized_parts = []
    
    for elem, count in sorted_elements:
        if count == 1:
            normalized_parts.append(elem)
        else:
            normalized_parts.append(f"{elem}{count}")
    
    return "".join(normalized_parts)

def get_source_priority(source: Optional[str]) -> int:
    """
    Get the priority of a data source (lower is better).
    
    Args:
        source: Source name string
        
    Returns:
        Priority integer (lower = higher priority)
    """
    if source is None:
        return SOURCE_PRIORITY["default"]
    
    # Case-insensitive matching
    source_lower = source.lower()
    for key, priority in SOURCE_PRIORITY.items():
        if key.lower() == source_lower:
            return priority
    
    return SOURCE_PRIORITY["default"]

def deduplicate_compositions(
    compositions: List[Dict[str, Any]],
    formula_field: str = "formula",
    source_field: str = "source"
) -> List[Dict[str, Any]]:
    """
    Deduplicate a list of compositions by unique chemical formula.
    
    When duplicates are found, the entry from the highest priority source
    is retained. Priority order: Science Advances > Materials Project/Zenodo > others.
    
    Args:
        compositions: List of composition dictionaries
        formula_field: Key name for the formula in each composition dict
        source_field: Key name for the source in each composition dict
        
    Returns:
        Deduplicated list of compositions
    """
    if not compositions:
        return []
    
    # Group by normalized formula
    formula_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    for comp in compositions:
        formula = comp.get(formula_field, "")
        normalized = normalize_formula(formula)
        if normalized:
            formula_groups[normalized].append(comp)
    
    # Select best entry from each group
    deduplicated = []
    
    for normalized_formula, group in formula_groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Sort by source priority (lower is better)
            sorted_group = sorted(
                group,
                key=lambda x: get_source_priority(x.get(source_field))
            )
            deduplicated.append(sorted_group[0])
    
    return deduplicated

def get_deduplication_stats(
    original: List[Dict[str, Any]],
    deduplicated: List[Dict[str, Any]],
    formula_field: str = "formula"
) -> Dict[str, Any]:
    """
    Calculate statistics about the deduplication process.
    
    Args:
        original: Original list of compositions
        deduplicated: Deduplicated list of compositions
        formula_field: Key name for the formula in each composition dict
        
    Returns:
        Dictionary with deduplication statistics
    """
    original_count = len(original)
    deduplicated_count = len(deduplicated)
    duplicates_removed = original_count - deduplicated_count
    
    # Count duplicates by source
    source_counts = defaultdict(int)
    formula_groups: Dict[str, List[str]] = defaultdict(list)
    
    for comp in original:
        formula = comp.get(formula_field, "")
        normalized = normalize_formula(formula)
        source = comp.get("source", "unknown")
        if normalized:
            formula_groups[normalized].append(source)
    
    # Count how many formulas had duplicates
    formulas_with_duplicates = sum(
        1 for group in formula_groups.values() if len(group) > 1
    )
    
    # Count retained sources
    retained_sources = defaultdict(int)
    for comp in deduplicated:
        source = comp.get("source", "unknown")
        retained_sources[source] += 1
    
    return {
        "original_count": original_count,
        "deduplicated_count": deduplicated_count,
        "duplicates_removed": duplicates_removed,
        "formulas_with_duplicates": formulas_with_duplicates,
        "retained_by_source": dict(retained_sources),
        "deduplication_rate": duplicates_removed / original_count if original_count > 0 else 0.0
    }
