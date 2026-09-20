"""
SC-005 Ratio Calculator

Calculates the SC-005 ratio: (number of species excluded due to n < 20) / (total number of species in input).
Reads from artifacts/reports/species_counts.json and writes to artifacts/reports/metrics.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_config, setup_logging


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calculate_sc005_ratio(species_counts: Dict[str, Any]) -> float:
    """
    Calculate SC-005 ratio: excluded_species_count / total_species_input.

    Args:
        species_counts: Dictionary containing 'total_species_input' and 'excluded_species_count'.

    Returns:
        The calculated ratio as a float.

    Raises:
        KeyError: If required keys are missing from the input dictionary.
        ZeroDivisionError: If total_species_input is zero.
    """
    total_species_input = species_counts.get('total_species_input')
    excluded_species_count = species_counts.get('excluded_species_count')

    if total_species_input is None or excluded_species_count is None:
        raise KeyError(
            "Missing required keys in species_counts.json. "
            "Expected 'total_species_input' and 'excluded_species_count'."
        )

    if total_species_input == 0:
        raise ZeroDivisionError("Total species input is zero; cannot calculate ratio.")

    ratio = excluded_species_count / total_species_input
    return float(ratio)


def main() -> int:
    """
    Main entry point for SC-005 ratio calculation.

    Reads species counts, calculates ratio, and updates metrics.json.
    Returns 0 on success, 1 on failure.
    """
    config = get_config()
    logger = setup_logging(config.get('LOG_LEVEL', 'INFO'))

    try:
        # Define paths
        species_counts_path = Path(config.get('ARTIFACTS_PATH', 'artifacts')) / 'reports' / 'species_counts.json'
        metrics_path = Path(config.get('ARTIFACTS_PATH', 'artifacts')) / 'reports' / 'metrics.json'

        logger.info(f"Loading species counts from: {species_counts_path}")
        species_counts = load_json_file(species_counts_path)

        logger.info(f"Calculating SC-005 ratio...")
        sc005_ratio = calculate_sc005_ratio(species_counts)

        logger.info(f"SC-005 Ratio calculated: {sc005_ratio:.4f}")
        logger.info(f"  - Total species input: {species_counts['total_species_input']}")
        logger.info(f"  - Excluded species count: {species_counts['excluded_species_count']}")

        # Load existing metrics or initialize
        metrics = {}
        if metrics_path.exists():
            logger.info(f"Loading existing metrics from: {metrics_path}")
            metrics = load_json_file(metrics_path)

        # Update metrics with SC-005 ratio
        metrics['species_exclusion_ratio'] = sc005_ratio
        metrics['sc005_calculation'] = {
            'excluded_species_count': species_counts['excluded_species_count'],
            'total_species_input': species_counts['total_species_input'],
            'formula': 'excluded_species_count / total_species_input'
        }

        # Save updated metrics
        logger.info(f"Writing updated metrics to: {metrics_path}")
        save_json_file(metrics_path, metrics)

        logger.info("SC-005 ratio calculation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except KeyError as e:
        logger.error(f"Key error: {e}")
        return 1
    except ZeroDivisionError as e:
        logger.error(f"Division by zero: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
