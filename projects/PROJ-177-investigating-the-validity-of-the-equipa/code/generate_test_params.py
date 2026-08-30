"""
Generate and save default test parameters for synthetic dataset generation.

This module defines the parameters for:
- Maxwell-Boltzmann distribution (thermal-like): mean=1.0, scale=0.1
- Pareto distribution (non-thermal-like): shape=2.0

Output: artifacts/test_params.json
"""
import json
import argparse
from pathlib import Path
from typing import Dict, Any


def get_default_test_params() -> Dict[str, Any]:
    """
    Return the default configuration for synthetic test datasets.
    
    Returns:
        Dict containing parameters for Maxwell-Boltzmann and Pareto distributions.
    """
    params = {
        "maxwell_boltzmann": {
            "mean": 1.0,
            "scale": 0.1,
            "description": "Thermal-like energy distribution (Maxwell-Boltzmann)"
        },
        "pareto": {
            "shape": 2.0,
            "description": "Non-thermal energy distribution (Pareto)"
        },
        "metadata": {
            "version": "1.0",
            "purpose": "Synthetic test data generation for pipeline validation"
        }
    }
    return params


def save_test_params(params: Dict[str, Any], output_path: Path) -> None:
    """
    Save test parameters to a JSON file.
    
    Args:
        params: Dictionary of parameters to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2)


def main() -> None:
    """CLI entry point to generate and save test parameters."""
    parser = argparse.ArgumentParser(
        description="Generate and save default test parameters for synthetic datasets."
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('artifacts/test_params.json'),
        help='Output path for the JSON file (default: artifacts/test_params.json)'
    )
    
    args = parser.parse_args()
    
    params = get_default_test_params()
    save_test_params(params, args.output)
    print(f"Test parameters saved to: {args.output}")


if __name__ == '__main__':
    main()
