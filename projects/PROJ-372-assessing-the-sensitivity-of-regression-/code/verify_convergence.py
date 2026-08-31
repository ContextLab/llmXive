"""
Verify that the Standard Error of the SD is < 5% (SC-005) and log the result.

This script reads the coefficient standard deviations and their standard errors
computed in T048/T050, checks the SC-005 criterion, and logs the outcome.
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def verify_sc005(
    sd_data: Dict[str, Any],
    threshold_percent: float = 5.0,
) -> Dict[str, Any]:
    """
    Verify SC-005: Standard Error of the SD must be < threshold_percent of the SD.
    
    Args:
        sd_data: Dictionary containing 'coefficient_sd' and 'se_of_sd' per tier.
        threshold_percent: Maximum allowed percentage (default 5.0%).
        
    Returns:
        Dictionary with verification results per tier and overall status.
    """
    results = {
        "threshold_percent": threshold_percent,
        "tiers": {},
        "overall_pass": True,
    }
    
    # Expecting structure like:
    # {
    #   "tiers": {
    #     "10": {"coefficient_sd": 0.12, "se_of_sd": 0.005},
    #     ...
    #   }
    # }
    tiers = sd_data.get("tiers", sd_data)
    
    for tier_name, data in tiers.items():
        sd = data.get("coefficient_sd")
        se = data.get("se_of_sd")
        
        if sd is None or se is None:
            results["tiers"][tier_name] = {
                "status": "error",
                "message": "Missing 'coefficient_sd' or 'se_of_sd'",
                "pass": False,
            }
            results["overall_pass"] = False
            continue
        
        if sd == 0:
            # Avoid division by zero; if SD is 0 and SE is 0, it's trivially passing
            # but if SE > 0, it's undefined. Treat as pass only if SE is also 0.
            ratio = 0.0 if se == 0 else float("inf")
        else:
            ratio = (se / sd) * 100.0
        
        passed = ratio < threshold_percent
        
        results["tiers"][tier_name] = {
            "coefficient_sd": sd,
            "se_of_sd": se,
            "ratio_percent": ratio,
            "status": "pass" if passed else "fail",
            "message": f"SE/SD = {ratio:.2f}% {'<' if passed else '>='} {threshold_percent}%",
            "pass": passed,
        }
        
        if not passed:
            results["overall_pass"] = False
    
    return results

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify SC-005: Standard Error of SD < 5% of SD"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/stability/coefficient_sd.json"),
        help="Path to coefficient_sd.json (output of T048/T050)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/meta_analysis/convergence_verification.json"),
        help="Path to write verification results",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Threshold percentage (default 5.0)",
    )
    
    args = parser.parse_args()
    
    # Load data
    try:
        sd_data = load_json_file(args.input)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {args.input}: {e}", file=sys.stderr)
        return 1
    
    # Verify
    results = verify_sc005(sd_data, args.threshold)
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    status = "PASS" if results["overall_pass"] else "FAIL"
    print(f"SC-005 Verification: {status}")
    for tier_name, tier_result in results["tiers"].items():
        print(f"  Tier {tier_name}: {tier_result['status']} ({tier_result['message']})")
    
    return 0 if results["overall_pass"] else 1

if __name__ == "__main__":
    sys.exit(main())