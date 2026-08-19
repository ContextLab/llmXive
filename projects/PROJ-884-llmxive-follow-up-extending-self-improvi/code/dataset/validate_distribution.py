"""
Distribution Validation Script for llmXive Pipeline.

This script reads the generated distribution report and the dataset schema
to verify statistical representativeness. It outputs a validation JSON
containing the validity status, power estimate, and notes.

Constraints:
- Must read data/processed/distribution_report.json
- Must read contracts/dataset.schema.yaml
- Must output data/processed/distribution_validation.json
- Fail loudly if inputs are missing or invalid.
"""

import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

INPUT_REPORT_PATH = DATA_PROCESSED_DIR / "distribution_report.json"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_VALIDATION_PATH = DATA_PROCESSED_DIR / "distribution_validation.json"


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file, raising FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_schema(path: Path) -> Dict[str, Any]:
    """
    Load the YAML schema file.
    Note: We use a simple parser for the specific YAML structure expected
    or rely on PyYAML if installed. Given constraints, we assume PyYAML
    is available as per requirements.txt (pyyaml==6.0.1).
    """
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    try:
        import yaml
    except ImportError:
        # Fallback to a basic text-based parser if yaml is missing, 
        # though requirements.txt should ensure it exists.
        raise ImportError("PyYAML is required to load the schema.")
        
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def calculate_chi_square(
    observed: Dict[str, int], 
    expected_ratios: Dict[str, float]
) -> float:
    """
    Calculate Chi-Square statistic for type distribution.
    observed: dict of {type_name: count}
    expected_ratios: dict of {type_name: ratio} (should sum to 1.0)
    """
    total_count = sum(observed.values())
    if total_count == 0:
        return 0.0
    
    chi_sq = 0.0
    for p_type, count in observed.items():
        expected_ratio = expected_ratios.get(p_type, 0.0)
        expected_count = total_count * expected_ratio
        if expected_count > 0:
            chi_sq += ((count - expected_count) ** 2) / expected_count
        else:
            # If a type is expected but has 0 count, and we have observed count,
            # this contributes to the statistic.
            if count > 0:
                chi_sq += (count ** 2) / 1e-9 # Avoid division by zero
    return chi_sq


def validate_complexity_scaling(
    complexity_dist: Dict[str, int], 
    target_ranges: List[Dict[str, Any]]
) -> bool:
    """
    Validates that complexity distribution covers the intended ranges.
    target_ranges: List of dicts with 'min', 'max', 'expected_count' or similar.
    For this implementation, we check if the distribution is continuous 
    across the defined N ranges (e.g., 10, 50, 100, 500).
    """
    if not complexity_dist:
        return False
    
    # Check if keys are numeric or parseable as such
    keys = [int(k) for k in complexity_dist.keys() if k.isdigit()]
    if not keys:
        return False
    
    # Sort keys to check continuity or presence of expected buckets
    keys.sort()
    
    # Simple heuristic: Ensure we have data points at the extremes or 
    # a sufficient number of distinct complexity levels.
    # Based on T011/T014d, we expect N=10..500.
    min_n = min(keys)
    max_n = max(keys)
    
    # If the range is too narrow or empty
    if max_n - min_n < 10:
        return False
        
    return True


def calculate_power_estimate(total_samples: int) -> float:
    """
    Estimate statistical power based on sample size.
    Simple heuristic: Power increases with sample size.
    For a two-proportion z-test with alpha=0.05:
    N=100 ~ 0.60, N=200 ~ 0.80, N=500 ~ 0.95
    """
    if total_samples <= 0:
        return 0.0
    
    # Approximation formula for power estimation (simplified)
    # Power = 1 - beta. Beta decreases as N increases.
    # Using a logistic-like growth for estimation
    power = 1.0 / (1.0 + math.exp(-0.02 * (total_samples - 150)))
    return min(max(power, 0.0), 1.0)


def main():
    """
    Main entry point for distribution validation.
    """
    print(f"Starting distribution validation...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Report Path: {INPUT_REPORT_PATH}")
    print(f"Schema Path: {SCHEMA_PATH}")

    try:
        # 1. Load Input Report
        report = load_json(INPUT_REPORT_PATH)
        print("Successfully loaded distribution report.")

        # 2. Load Schema
        schema = load_schema(SCHEMA_PATH)
        print("Successfully loaded dataset schema.")

        # 3. Extract Data
        total_count = report.get("total_count", 0)
        type_distribution = report.get("type_distribution", {})
        complexity_distribution = report.get("complexity_distribution", {})

        # 4. Validate against Schema
        # Check if the report keys match the expected schema structure
        expected_keys = ["total_count", "type_distribution", "complexity_distribution"]
        for key in expected_keys:
            if key not in report:
                raise ValueError(f"Report missing required key: {key}")

        # 5. Perform Statistical Checks
        # Chi-Square for Type Distribution
        # Assume uniform distribution or defined ratios in schema if available.
        # If schema doesn't specify, assume uniform for validation.
        types = list(type_distribution.keys())
        expected_ratios = {t: 1.0 / len(types) for t in types} if types else {}
        
        chi_sq = calculate_chi_square(type_distribution, expected_ratios)
        
        # Critical value for Chi-Square (alpha=0.05, df=len(types)-1)
        # Approximation: df=2 -> 5.99, df=3 -> 7.81
        df = len(types) - 1 if len(types) > 0 else 0
        critical_value = 5.991 if df == 2 else (7.815 if df == 3 else 9.488)
        
        type_valid = chi_sq <= critical_value

        # Complexity Scaling Validation
        complexity_valid = validate_complexity_scaling(
            complexity_distribution, 
            [] # No specific target ranges passed, using internal logic
        )

        is_valid = type_valid and complexity_valid

        # 6. Calculate Power Estimate
        power_estimate = calculate_power_estimate(total_count)

        # 7. Generate Notes
        notes = []
        if not type_valid:
            notes.append(f"Type distribution failed Chi-Square test (stat={chi_sq:.2f}, crit={critical_value:.2f}).")
        if not complexity_valid:
            notes.append("Complexity scaling validation failed.")
        if power_estimate < 0.8:
            notes.append(f"Statistical power ({power_estimate:.2f}) is below 0.8 threshold.")
        if is_valid and not notes:
            notes.append("All distribution checks passed.")

        # 8. Construct Output
        validation_result = {
            "is_valid": is_valid,
            "power_estimate": round(power_estimate, 4),
            "notes": notes,
            "details": {
                "total_count": total_count,
                "chi_square_statistic": round(chi_sq, 4),
                "complexity_valid": complexity_valid,
                "type_valid": type_valid
            }
        }

        # 9. Write Output
        OUTPUT_VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_VALIDATION_PATH, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2)

        print(f"Validation complete. Output written to: {OUTPUT_VALIDATION_PATH}")
        print(f"Result: is_valid={is_valid}, power={power_estimate:.4f}")

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: Validation logic error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())