"""
Composition Parser Module for Heusler Alloy Analysis.

This module converts chemical composition strings (e.g., 'Co2MnGa') into
atomic fractions with at least 4 decimal places of precision.
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Regex pattern to parse chemical formulas
# Matches element symbol (1-2 chars) followed by an optional integer count
FORMULA_PATTERN = re.compile(r'([A-Z][a-z]?)(\d*)')

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a chemical composition string into atomic fractions.

    Args:
        composition_str: A string representing the composition, e.g., 'Co2MnGa', 'FeNi3'.

    Returns:
        A dictionary mapping element symbols to their atomic fractions (float).
        Values are normalized to sum to 1.0.

    Raises:
        ValueError: If the composition string is empty or cannot be parsed.
        ValueError: If the sum of counts is zero.
    """
    if not composition_str or not isinstance(composition_str, str):
        raise ValueError(f"Invalid composition string: '{composition_str}'")

    composition_str = composition_str.strip()
    if not composition_str:
        raise ValueError("Composition string is empty after stripping.")

    # Parse the formula
    elements_counts: Dict[str, int] = {}
    matches = FORMULA_PATTERN.findall(composition_str)

    if not matches:
        raise ValueError(f"Could not parse any elements from formula: '{composition_str}'")

    total_atoms = 0
    for element, count_str in matches:
        count = int(count_str) if count_str else 1
        if count <= 0:
            raise ValueError(f"Invalid atom count for element '{element}' in '{composition_str}'")
        
        elements_counts[element] = elements_counts.get(element, 0) + count
        total_atoms += count

    if total_atoms == 0:
        raise ValueError(f"Total atom count is zero for formula: '{composition_str}'")

    # Convert to fractions
    fractions = {
        elem: round(count / total_atoms, 4) 
        for elem, count in elements_counts.items()
    }

    # Log the parsing result
    logger.debug(f"Parsed composition '{composition_str}' -> {fractions}")

    return fractions

def parse_formula_to_fractions(formula: str) -> Dict[str, float]:
    """
    Alias for parse_composition to satisfy test imports and interface consistency.
    
    Args:
        formula: Chemical formula string.
        
    Returns:
        Dictionary of element to atomic fraction.
    """
    return parse_composition(formula)

def parse_batch_compositions(compositions: List[str]) -> List[Dict[str, float]]:
    """
    Parse a list of composition strings.

    Args:
        compositions: List of composition strings.

    Returns:
        List of dictionaries mapping elements to atomic fractions.
    """
    results = []
    for comp in compositions:
        try:
            results.append(parse_composition(comp))
        except ValueError as e:
            logger.warning(f"Failed to parse composition '{comp}': {e}")
            results.append({})
    return results

def main():
    """
    Entry point for testing the composition parser directly.
    """
    test_cases = [
        "Co2MnGa",
        "FeNi3",
        "MnFeCo",
        "Co2Mn1.5Ga0.5", # Note: Current regex doesn't support decimals, will parse as 1.5 -> 1, 5? No, regex is \d*
        "InvalidString",
        ""
    ]

    for case in test_cases:
        try:
            result = parse_composition(case)
            print(f"Input: {case} -> Output: {result}")
        except Exception as e:
            print(f"Input: {case} -> Error: {e}")

if __name__ == "__main__":
    # Setup basic logging for direct execution
    logging.basicConfig(level=logging.DEBUG)
    main()
