"""
Parameter Coverage Calculation Utilities.

This module implements logic to calculate Parameter Coverage Scores
using `docstring_parser` for text-based parameter extraction from docstrings.
It compares extracted docstring parameters against function signature parameters
(provided via AST) to determine coverage.

Note: This implementation focuses on text parsing only (docstring_parser)
and does not perform complex type hint matching logic (handled in T033/T038).
"""

import logging
from typing import List, Optional, Tuple, Dict, Any

import docstring_parser
from docstring_parser import Docstring, DocstringParam

logger = logging.getLogger(__name__)


class CoverageException(Exception):
    """Exception raised when coverage calculation fails."""
    pass


def parse_docstring_parameters(docstring_text: Optional[str]) -> List[str]:
    """
    Extract parameter names from a docstring text using docstring_parser.

    Args:
        docstring_text: The raw docstring text (stripped of surrounding quotes).
                        Can be None or empty.

    Returns:
        A list of parameter names found in the docstring.
        Returns an empty list if no parameters are found or parsing fails.
    """
    if not docstring_text or not docstring_text.strip():
        return []

    try:
        parsed: Docstring = docstring_parser.parse(docstring_text)
        params: List[DocstringParam] = parsed.params

        # Extract just the arg names
        arg_names = [p.arg_name for p in params if p.arg_name]

        # Normalize names (remove leading colons or dots if present in some formats)
        normalized_names = []
        for name in arg_names:
            # Handle cases like ":param x:" or "x:"
            clean_name = name.split(":")[0].strip()
            if clean_name:
                normalized_names.append(clean_name)

        return normalized_names

    except Exception as e:
        logger.warning(f"Failed to parse docstring for parameters: {e}")
        return []


def calculate_parameter_coverage(
    ast_params: List[str],
    docstring_text: Optional[str]
) -> Tuple[float, int, int, List[str]]:
    """
    Calculate the parameter coverage score.

    Coverage is defined as: (number of AST parameters found in docstring) / (total AST parameters).

    Args:
        ast_params: List of parameter names extracted from the AST function signature.
        docstring_text: The raw docstring text associated with the function.

    Returns:
        A tuple containing:
            - score (float): The coverage ratio (0.0 to 1.0).
            - matched_count (int): Number of AST params found in docstring.
            - total_count (int): Total number of AST params.
            - missing_params (List[str]): List of AST params NOT found in docstring.

    Raises:
        CoverageException: If input types are invalid.
    """
    if not isinstance(ast_params, list):
        raise CoverageException(f"ast_params must be a list, got {type(ast_params)}")

    total_count = len(ast_params)

    if total_count == 0:
        # If there are no parameters, coverage is technically 1.0 (vacuously true)
        # or 0.0 depending on interpretation. We return 1.0 as no params are missing.
        return 1.0, 0, 0, []

    docstring_params = parse_docstring_parameters(docstring_text)
    docstring_set = set(docstring_params)

    matched_count = 0
    missing_params = []

    for param in ast_params:
        # Normalize AST param name for comparison (strip self, cls if needed, though AST usually clean)
        clean_param = param.strip()
        if clean_param in docstring_set:
            matched_count += 1
        else:
            missing_params.append(clean_param)

    score = matched_count / total_count

    return score, matched_count, total_count, missing_params


def calculate_coverage_batch(
    methods: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a batch of method data to calculate coverage scores.

    Args:
        methods: List of dicts containing 'ast_params' (list of str) and 'docstring_text' (str or None).

    Returns:
        List of enriched method dicts with added keys:
            - 'coverage_score'
            - 'matched_params_count'
            - 'total_params_count'
            - 'missing_params'
    """
    results = []
    for idx, method in enumerate(methods):
        try:
            ast_params = method.get("ast_params", [])
            docstring_text = method.get("docstring_text")

            score, matched, total, missing = calculate_parameter_coverage(
                ast_params, docstring_text
            )

            enriched = method.copy()
            enriched["coverage_score"] = score
            enriched["matched_params_count"] = matched
            enriched["total_params_count"] = total
            enriched["missing_params"] = missing

            results.append(enriched)

        except Exception as e:
            logger.error(f"Error processing method at index {idx}: {e}")
            # Include the method with null scores to indicate failure
            enriched = method.copy()
            enriched["coverage_score"] = None
            enriched["matched_params_count"] = None
            enriched["total_params_count"] = None
            enriched["missing_params"] = None
            enriched["coverage_error"] = str(e)
            results.append(enriched)

    return results