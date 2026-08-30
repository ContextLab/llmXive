"""
Deduplication utility for chemical compositions.
Normalizes chemical formulas and removes duplicate entries based on unique composition.
"""
from typing import Dict, List, Any, Optional, Tuple
import re
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_formula(formula: str) -> str:
    """
    Normalize a chemical formula string to a canonical form.
    Steps:
    1. Remove spaces and convert to standard capitalization.
    2. Sort elements alphabetically.
    3. Normalize stoichiometric coefficients to integers or simple fractions.
    4. Return a string like "Al2Cu" or "Al2Cu3".

    Args:
        formula: Raw formula string (e.g., "Cu_2Al", "Al2Cu", "Cu2 Al").

    Returns:
        Normalized formula string.
    """
    if not formula:
        return ""

    # Clean string
    s = formula.replace('_', '').replace(' ', '').strip()

    # Parse elements and counts
    # Regex: Element (1-2 chars) followed by optional number
    pattern = r'([A-Z][a-z]?)(\d*(?:\.\d+)?)'
    matches = re.findall(pattern, s)

    if not matches:
        return s # Return original if no match

    elements = defaultdict(float)
    for elem, count_str in matches:
        count = float(count_str) if count_str else 1.0
        elements[elem] += count

    # Normalize counts to integers if possible (e.g., 1.5 -> 3/2)
    # Find common denominator or scale to integers
    # Simple approach: multiply by 100, round, then divide by GCD
    counts = [elements[e] for e in sorted(elements.keys())]
    
    # Check if all are integers (within tolerance)
    if all(abs(c - round(c)) < 1e-6 for c in counts):
        int_counts = [int(round(c)) for c in counts]
    else:
        # Scale to integers (approximate)
        # Find smallest non-zero, scale up
        min_val = min(c for c in counts if c > 0)
        scale = 100 # Heuristic
        int_counts = [int(round(c * scale)) for c in counts]

    # Divide by GCD of all counts
    from math import gcd
    from functools import reduce
    overall_gcd = reduce(gcd, int_counts)
    int_counts = [c // overall_gcd for c in int_counts]

    # Reconstruct string
    sorted_elements = sorted(elements.keys())
    parts = []
    for elem in sorted_elements:
        count = int_counts[sorted_elements.index(elem)]
        if count == 1:
            parts.append(elem)
        else:
            parts.append(f"{elem}{count}")
    
    return "".join(parts)

def get_source_priority(source: str) -> int:
    """
    Return priority for data source. Higher is better.
    Materials Project > Zenodo > Synthetic
    """
    priorities = {
        'materials_project': 3,
        'zenodo': 2,
        'synthetic': 1
    }
    return priorities.get(source.lower(), 0)

def deduplicate_compositions(
    data: List[Dict[str, Any]],
    formula_col: str = 'composition',
    source_col: str = 'source'
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Deduplicate a list of composition records.
    Keeps the record with the highest source priority for each unique normalized formula.

    Args:
        data: List of dictionaries containing composition data.
        formula_col: Key for the composition string.
        source_col: Key for the source string.

    Returns:
        Tuple of (deduplicated_list, stats_dict)
    """
    seen: Dict[str, Dict[str, Any]] = {}
    stats = defaultdict(int)

    for record in data:
        raw_formula = record.get(formula_col, "")
        source = record.get(source_col, "unknown")
        
        if not raw_formula:
            stats['empty_formula'] += 1
            continue

        normalized = normalize_formula(raw_formula)
        stats['total_processed'] += 1

        if normalized not in seen:
            seen[normalized] = record
        else:
            existing_source = seen[normalized].get(source_col, "unknown")
            if get_source_priority(source) > get_source_priority(existing_source):
                seen[normalized] = record
                stats['replaced_lower_priority'] += 1
            else:
                stats['skipped_lower_priority'] += 1

    deduped_list = list(seen.values())
    stats['unique_count'] = len(deduped_list)
    stats['duplicates_removed'] = stats['total_processed'] - len(deduped_list)

    return deduped_list, dict(stats)

def get_deduplication_stats(stats: Dict[str, int]) -> str:
    """
    Format stats into a human-readable string.
    """
    if not stats:
        return "No deduplication performed."
    
    lines = [
        f"Total processed: {stats.get('total_processed', 0)}",
        f"Unique formulas: {stats.get('unique_count', 0)}",
        f"Duplicates removed: {stats.get('duplicates_removed', 0)}",
        f"Replaced by higher priority: {stats.get('replaced_lower_priority', 0)}",
        f"Skipped (lower priority): {stats.get('skipped_lower_priority', 0)}"
    ]
    return "\n".join(lines)
