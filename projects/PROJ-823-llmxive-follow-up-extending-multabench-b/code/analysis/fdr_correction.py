import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Perform Benjamini-Hochberg FDR correction on a list of p-values.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of (adjusted_p_values, significance_flags)
        adjusted_p_values: List of FDR-adjusted p-values.
        significance_flags: List of booleans indicating if the result is significant after correction.
    """
    if not p_values:
        return [], []

    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]

    adjusted_p_values = [0.0] * n
    rank = 1

    # Calculate adjusted p-values from smallest to largest
    # BH procedure: p_adj(i) = p(i) * n / i
    # Ensure monotonicity by taking min with previous adjusted value
    prev_adj = 1.0
    for i in range(n - 1, -1, -1):
        current_p = sorted_p_values[i]
        # BH formula
        adjusted = current_p * n / (i + 1)
        # Enforce monotonicity (adjusted p-values should not decrease as rank increases)
        adjusted = min(adjusted, prev_adj)
        # Cap at 1.0
        adjusted = min(adjusted, 1.0)
        adjusted_p_values[sorted_indices[i]] = adjusted
        prev_adj = adjusted

    # Determine significance
    significance_flags = [p <= alpha for p in adjusted_p_values]

    return adjusted_p_values, significance_flags

def load_p_values_from_file(file_path: Path) -> Dict[str, List[float]]:
    """
    Load p-values from a JSON file. Expected structure:
    {
        "correlation": {"feature_name": p_value, ...},
        "t_test": {"dataset_id": p_value, ...}
    }
    """
    if not file_path.exists():
        raise FileNotFoundError(f"P-values file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    return data

def save_adjusted_p_values(output_path: Path, results: Dict[str, Dict[str, Any]]) -> None:
    """
    Save adjusted p-values to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    log_info(f"Adjusted p-values saved to {output_path}")

def process_correlation_p_values(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process correlation p-values: apply BH correction and return results.
    """
    features = list(p_values.keys())
    raw_p_values = list(p_values.values())

    adjusted_p_values, significance_flags = benjamini_hochberg(raw_p_values, alpha)

    results = {
        "raw_p_values": p_values,
        "adjusted_p_values": dict(zip(features, adjusted_p_values)),
        "significant": dict(zip(features, significance_flags)),
        "method": "Benjamini-Hochberg",
        "alpha": alpha,
        "num_tests": len(p_values)
    }

    return results

def process_t_test_p_values(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process t-test p-values: apply BH correction and return results.
    """
    dataset_ids = list(p_values.keys())
    raw_p_values = list(p_values.values())

    adjusted_p_values, significance_flags = benjamini_hochberg(raw_p_values, alpha)

    results = {
        "raw_p_values": p_values,
        "adjusted_p_values": dict(zip(dataset_ids, adjusted_p_values)),
        "significant": dict(zip(dataset_ids, significance_flags)),
        "method": "Benjamini-Hochberg",
        "alpha": alpha,
        "num_tests": len(p_values)
    }

    return results

def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main function to run FDR correction on p-values from correlation and t-test analyses.

    Args:
        args: Command line arguments (optional, for testing)

    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(description="Apply Benjamini-Hochberg FDR correction to p-values")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSON file containing p-values from T033 (correlation) and T035 (t-test)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON file with adjusted p-values"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for FDR correction (default: 0.05)"
    )

    if args is None:
        args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        log_info(f"Loading p-values from {input_path}")
        raw_data = load_p_values_from_file(input_path)

        results = {
            "correlation_analysis": {},
            "t_test_analysis": {},
            "summary": {}
        }

        # Process correlation p-values
        if "correlation" in raw_data:
            log_info("Processing correlation p-values")
            results["correlation_analysis"] = process_correlation_p_values(raw_data["correlation"], args.alpha)
            significant_count = sum(results["correlation_analysis"]["significant"].values())
            results["summary"]["correlation_significant_count"] = significant_count
            results["summary"]["correlation_total_tests"] = len(raw_data["correlation"])

        # Process t-test p-values
        if "t_test" in raw_data:
            log_info("Processing t-test p-values")
            results["t_test_analysis"] = process_t_test_p_values(raw_data["t_test"], args.alpha)
            significant_count = sum(results["t_test_analysis"]["significant"].values())
            results["summary"]["t_test_significant_count"] = significant_count
            results["summary"]["t_test_total_tests"] = len(raw_data["t_test"])

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        save_adjusted_p_values(output_path, results)

        log_info(f"FDR correction completed successfully. Results saved to {output_path}")
        return 0

    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error during FDR correction: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
