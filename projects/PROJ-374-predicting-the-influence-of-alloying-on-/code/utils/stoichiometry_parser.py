"""
Stoichiometry Parser Module

Provides functions to parse chemical formulas into normalized elemental
compositions and perform basic stoichiometric calculations.
"""
import re
from typing import Dict, Tuple, Union, Optional
from collections import Counter

# Regex pattern to match chemical formulas
# Matches element symbols (1-2 letters, first uppercase) followed by optional number
FORMULA_PATTERN = re.compile(r'([A-Z][a-z]?)(\d*)')


def parse_formula(formula: str) -> Dict[str, int]:
    """
    Parse a chemical formula string into a dictionary of elements and their counts.

    Args:
        formula: Chemical formula string (e.g., "Bi2Te3", "PbTe", "Co4Sb12")

    Returns:
        Dictionary mapping element symbols to their stoichiometric counts

    Raises:
        ValueError: If the formula is invalid or empty
        TypeError: If formula is not a string
    """
    if not isinstance(formula, str):
        raise TypeError(f"Formula must be a string, got {type(formula)}")

    formula = formula.strip()
    if not formula:
        raise ValueError("Formula cannot be empty")

    # Validate formula format (basic check)
    if not re.match(r'^[A-Z][a-z]?\d?([A-Z][a-z]?\d?)*$', formula):
        raise ValueError(f"Invalid chemical formula format: {formula}")

    matches = FORMULA_PATTERN.findall(formula)
    if not matches:
        raise ValueError(f"Could not parse formula: {formula}")

    composition = {}
    for element, count_str in matches:
        count = int(count_str) if count_str else 1
        composition[element] = composition.get(element, 0) + count

    return composition


def normalize_formula(composition: Dict[str, int]) -> Dict[str, float]:
    """
    Normalize a composition dictionary to sum to 1.0 (mole fractions).

    Args:
        composition: Dictionary mapping element symbols to counts

    Returns:
        Dictionary mapping element symbols to normalized mole fractions

    Raises:
        ValueError: If total count is zero or composition is empty
    """
    if not composition:
        raise ValueError("Cannot normalize empty composition")

    total = sum(composition.values())
    if total == 0:
        raise ValueError("Total composition count is zero")

    return {element: count / total for element, count in composition.items()}


def get_total_atoms(composition: Dict[str, int]) -> int:
    """
    Calculate the total number of atoms in a composition.

    Args:
        composition: Dictionary mapping element symbols to counts

    Returns:
        Total number of atoms
    """
    return sum(composition.values())


def parse_and_normalize(formula: str) -> Tuple[Dict[str, int], Dict[str, float]]:
    """
    Parse a formula and return both integer counts and normalized fractions.

    Args:
        formula: Chemical formula string

    Returns:
        Tuple of (integer composition, normalized mole fractions)
    """
    composition = parse_formula(formula)
    normalized = normalize_formula(composition)
    return composition, normalized


def validate_elements(composition: Dict[str, int], valid_elements: Optional[set] = None) -> bool:
    """
    Validate that all elements in a composition are in a set of valid elements.

    Args:
        composition: Dictionary mapping element symbols to counts
        valid_elements: Set of valid element symbols (optional)

    Returns:
        True if all elements are valid, False otherwise
    """
    if valid_elements is None:
        return True  # No validation required

    return all(element in valid_elements for element in composition.keys())


def combine_compositions(compositions: list) -> Dict[str, int]:
    """
    Combine multiple composition dictionaries into one.

    Args:
        compositions: List of composition dictionaries

    Returns:
        Combined composition dictionary
    """
    combined = Counter()
    for comp in compositions:
        combined.update(comp)
    return dict(combined)