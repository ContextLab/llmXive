"""
write_scaling_results.py

Implements Task T025:
Read the optimal scaling factor `s` and its CI from the output of T022/T023
and write to `data/derived/scaling_factor.txt`.

This module provides functions to load the computed scaling results from
`derive_scaling.py` and write them to a human-readable, parsable text file.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules using the exact public API surface provided
from logger import get_logger, info, error
from derive_scaling import fit_scaling_factor, bootstrap_scaling_analysis, load_raw_energies

# Initialize logger
logger = get_logger(__name__)

def load_scaling_results(
    scaling_output_path: str = "data/derived/scaling_results.json"
) -> Dict[str, Any]:
    """
    Load the scaling results computed by derive_scaling.py.

    Args:
        scaling_output_path: Path to the JSON file containing scaling results.

    Returns:
        Dictionary containing the scaling factor, confidence interval, and metadata.

    Raises:
        FileNotFoundError: If the scaling results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(scaling_output_path)
    if not path.exists():
        error(f"Scaling results file not found: {scaling_output_path}")
        raise FileNotFoundError(f"Scaling results file not found: {scaling_output_path}")

    with open(path, 'r') as f:
        results = json.load(f)

    info(f"Loaded scaling results from {scaling_output_path}")
    return results

def write_scaling_file(
    results: Dict[str, Any],
    output_path: str = "data/derived/scaling_factor.txt"
) -> None:
    """
    Write the optimal scaling factor and its confidence interval to a text file.

    This function implements the core requirement of Task T025: reading the
    optimal scaling factor `s` and its CI from the output of T022/T023 and
    writing it to `data/derived/scaling_factor.txt` in a human-readable,
    parsable format.

    Args:
        results: Dictionary containing scaling factor, CI, and metadata.
        output_path: Path to the output text file.

    Raises:
        ValueError: If required keys are missing from results.
    """
    # Validate required keys
    required_keys = ['optimal_s', 'ci_lower', 'ci_upper', 'hypothesis_test_passed']
    for key in required_keys:
        if key not in results:
            error(f"Missing required key in results: {key}")
            raise ValueError(f"Missing required key in results: {key}")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Format the output as human-readable text
    lines = [
        "=" * 60,
        "DFT-D3 Scaling Factor Results for Ionic Liquids",
        "=" * 60,
        "",
        "Optimal Scaling Factor (s):",
        f"  Value: {results['optimal_s']:.6f}",
        "",
        "95% Confidence Interval:",
        f"  Lower Bound: {results['ci_lower']:.6f}",
        f"  Upper Bound: {results['ci_upper']:.6f}",
        "",
        "Hypothesis Test (s = 1.0):",
        f"  Result: {'PASSED' if results['hypothesis_test_passed'] else 'FAILED'}",
        f"  Interpretation: {'The CI excludes 1.0, indicating significant deviation from unity.' if results['hypothesis_test_passed'] else 'The CI includes 1.0, no significant deviation from unity.'}",
        "",
        "Metadata:",
        f"  Bootstrap Replicates: {results.get('bootstrap_replicates', 'N/A')}",
        f"  Dataset Size: {results.get('dataset_size', 'N/A')} pairs",
        f"  Objective: Minimize MAE of corrected energies",
        "",
        "Note: This dataset (20 pairs) is underpowered for the Spec's intended",
        "statistical significance (≥100 pairs). CIs are for descriptive purposes only.",
        "=" * 60,
    ]

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))

    info(f"Scaling factor results written to {output_path}")

def main() -> None:
    """
    Main entry point for Task T025.

    This function orchestrates the workflow:
    1. Load raw energies (to ensure T022/T023 have been run)
    2. Load the scaling results from derive_scaling.py output
    3. Write the scaling factor and CI to data/derived/scaling_factor.txt
    """
    info("Starting Task T025: Write scaling factor results")

    try:
        # Define paths
        raw_energies_path = "data/derived/raw_energies.csv"
        scaling_results_path = "data/derived/scaling_results.json"
        output_path = "data/derived/scaling_factor.txt"

        # Verify raw energies exist (dependency T017)
        if not Path(raw_energies_path).exists():
            error(f"Raw energies file not found: {raw_energies_path}")
            error("Please run T017 (analyze_energies.py) before T025.")
            raise FileNotFoundError(f"Raw energies file not found: {raw_energies_path}")

        # Load scaling results (output of T022/T023/T024)
        info(f"Loading scaling results from {scaling_results_path}")
        results = load_scaling_results(scaling_results_path)

        # Write the scaling factor file
        write_scaling_file(results, output_path)

        info("Task T025 completed successfully.")

    except Exception as e:
        error(f"Task T025 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()