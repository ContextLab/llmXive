"""
Sweep Thresholds Module for Compressibility Analysis.

This module implements the logic to generate multiple compressed rule sets
by sweeping a compression/pruning threshold across the global rule set.
It produces a collection of rule sets and a metadata file describing the sweep.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import shutil

# Import config and utilities from project root
from config import get_config

class SweepThresholdsError(Exception):
    """Custom exception for sweep threshold errors."""
    pass

def load_global_rules(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load the global rule set from the aggregated rules file.

    Args:
        config: Configuration dictionary containing paths.

    Returns:
        List of rule dictionaries.

    Raises:
        SweepThresholdsError: If the file is missing or invalid.
    """
    rules_path = Path(config["paths"]["global_rules"])
    if not rules_path.exists():
        raise SweepThresholdsError(
            f"Global rules file not found at {rules_path}. "
            "Please ensure T026b has been completed successfully."
        )

    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        if not isinstance(rules, list):
            raise SweepThresholdsError("Global rules file must contain a JSON list of rules.")
        return rules
    except json.JSONDecodeError as e:
        raise SweepThresholdsError(f"Invalid JSON in global rules file: {e}")

def prune_rules_by_min_support(rules: List[Dict[str, Any]], min_support: float) -> List[Dict[str, Any]]:
    """
    Filter rules based on a minimum support threshold.

    Args:
        rules: List of rule dictionaries.
        min_support: Minimum support value (0.0 to 1.0).

    Returns:
        Filtered list of rules.
    """
    return [r for r in rules if r.get("support", 0.0) >= min_support]

def prune_rules_by_max_depth(rules: List[Dict[str, Any]], max_depth: int) -> List[Dict[str, Any]]:
    """
    Filter rules based on a maximum depth threshold.

    Args:
        rules: List of rule dictionaries.
        max_depth: Maximum allowed depth.

    Returns:
        Filtered list of rules.
    """
    return [r for r in rules if r.get("depth", 0) <= max_depth]

def prune_rules_by_count(rules: List[Dict[str, Any]], max_count: int) -> List[Dict[str, Any]]:
    """
    Truncate the rule list to a maximum count (sorted by support descending).

    Args:
        rules: List of rule dictionaries.
        max_count: Maximum number of rules to keep.

    Returns:
        Truncated list of rules.
    """
    sorted_rules = sorted(rules, key=lambda x: x.get("support", 0.0), reverse=True)
    return sorted_rules[:max_count]

def apply_pruning(
    rules: List[Dict[str, Any]],
    method: str,
    threshold: Any
) -> List[Dict[str, Any]]:
    """
    Apply a specific pruning method to the rule set.

    Args:
        rules: Original rule set.
        method: Pruning method ('min_support', 'max_depth', 'max_count').
        threshold: Threshold value for the method.

    Returns:
        Pruned rule set.
    """
    if method == "min_support":
        return prune_rules_by_min_support(rules, float(threshold))
    elif method == "max_depth":
        return prune_rules_by_max_depth(rules, int(threshold))
    elif method == "max_count":
        return prune_rules_by_count(rules, int(threshold))
    else:
        raise SweepThresholdsError(f"Unknown pruning method: {method}")

def calculate_compression_ratio(original_count: int, pruned_count: int) -> float:
    """
    Calculate the compression ratio.

    Args:
        original_count: Number of rules in original set.
        pruned_count: Number of rules in pruned set.

    Returns:
        Compression ratio (pruned / original).
    """
    if original_count == 0:
        return 0.0
    return pruned_count / original_count

def run_sweep(
    rules: List[Dict[str, Any]],
    output_dir: Path,
    sweep_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute the threshold sweep and save results.

    Args:
        rules: The global rule set.
        output_dir: Directory to save sweep outputs.
        sweep_config: Configuration for the sweep (methods, ranges).

    Returns:
        Metadata dictionary about the sweep execution.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    original_count = len(rules)
    results = []

    # Iterate over configured methods and ranges
    for method_config in sweep_config.get("sweep_methods", []):
        method = method_config["method"]
        param_name = method_config["param"]
        values = method_config["values"]

        for value in values:
            pruned_rules = apply_pruning(rules, method, value)
            pruned_count = len(pruned_rules)
            compression_ratio = calculate_compression_ratio(original_count, pruned_count)

            # Save the pruned rule set
            safe_value = str(value).replace(".", "_").replace(":", "_")
            filename = f"rules_{method}_{safe_value}.json"
            save_path = output_dir / filename

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(pruned_rules, f, indent=2)

            results.append({
                "method": method,
                "param": param_name,
                "threshold": value,
                "original_count": original_count,
                "pruned_count": pruned_count,
                "compression_ratio": compression_ratio,
                "output_file": str(save_path)
            })

    return {
        "total_sweeps": len(results),
        "original_rule_count": original_count,
        "sweep_parameters": sweep_config,
        "results": results
    }

def main():
    """Main entry point for the sweep thresholds script."""
    config = get_config()
    paths = config["paths"]

    # Load global rules
    print("Loading global rules...")
    try:
        rules = load_global_rules(config)
        print(f"Loaded {len(rules)} global rules.")
    except SweepThresholdsError as e:
        print(f"Error loading global rules: {e}")
        sys.exit(1)

    # Define sweep configuration
    # We sweep min_support from 0.0 to 0.9 in steps of 0.1
    sweep_config = {
        "sweep_methods": [
            {
                "method": "min_support",
                "param": "min_support",
                "values": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            },
            {
                "method": "max_depth",
                "param": "max_depth",
                "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ]
    }

    # Ensure output directory exists
    sweeps_dir = Path(paths["sweep_rules"])
    sweeps_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running sweep on {len(rules)} rules...")
    try:
        metadata = run_sweep(rules, sweeps_dir, sweep_config)
    except SweepThresholdsError as e:
        print(f"Sweep execution failed: {e}")
        sys.exit(1)

    # Save metadata
    metadata_path = Path(paths["sweep_config"])
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"Sweep complete. Results saved to {sweeps_dir}")
    print(f"Metadata saved to {metadata_path}")
    print(f"Total configurations generated: {metadata['total_sweeps']}")

if __name__ == "__main__":
    main()
