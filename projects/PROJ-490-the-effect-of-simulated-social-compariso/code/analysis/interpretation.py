"""
Dynamic interpretation logic for the analysis pipeline.

This module implements the logic to differentiate between "Empirical Association"
(for real data) and "Simulated Causal Effect" (for synthetic data) as per FR-010.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from data.config import get_config

logger = logging.getLogger(__name__)


def determine_interpretation_label(data_source_type: str) -> str:
    """
    Determine the correct interpretation label based on the data source type.

    Args:
        data_source_type: The type of data source used ('real' or 'synthetic').

    Returns:
        str: The interpretation label ("Empirical Association" or "Simulated Causal Effect").

    Raises:
        ValueError: If data_source_type is not recognized.
    """
    if data_source_type == "real":
        return "Empirical Association"
    elif data_source_type == "synthetic":
        return "Simulated Causal Effect"
    else:
        raise ValueError(f"Unknown data_source_type: {data_source_type}. Must be 'real' or 'synthetic'.")


def generate_interpretation_summary(
    results: Dict[str, Any],
    data_source_type: str,
    coefficients: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Generate a summary of results with the appropriate dynamic interpretation label.

    Args:
        results: Dictionary containing model results (coefficients, p-values, diagnostics).
        data_source_type: The type of data source used ('real' or 'synthetic').
        coefficients: Optional dictionary of specific coefficients to highlight.

    Returns:
        Dict[str, Any]: A dictionary containing the interpretation label and the results.
    """
    interpretation_label = determine_interpretation_label(data_source_type)
    logger.info(f"Generating interpretation summary with label: {interpretation_label}")

    summary = {
        "interpretation_label": interpretation_label,
        "data_source_type": data_source_type,
        "results": results
    }

    if coefficients:
        summary["highlighted_coefficients"] = coefficients

    return summary


def run_interpretation(
    results_path: Path,
    data_source_type: str,
    output_path: Path
) -> Dict[str, Any]:
    """
    Load results, apply dynamic interpretation, and save the final summary.

    This function acts as the entry point for the interpretation logic, ensuring
    that the output artifacts correctly reflect the nature of the data source.

    Args:
        results_path: Path to the JSON file containing regression results.
        data_source_type: The type of data source used ('real' or 'synthetic').
        output_path: Path where the interpreted summary JSON will be saved.

    Returns:
        Dict[str, Any]: The generated interpretation summary.
    """
    import json

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}")

    with open(results_path, 'r') as f:
        results = json.load(f)

    summary = generate_interpretation_summary(results, data_source_type)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Interpretation summary saved to {output_path}")
    return summary
