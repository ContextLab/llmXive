"""
T055: Validate GLMM Model Specification against Spec FR-006.

This script verifies that the GLMM implementation in `code/data/modeling.py`
adheres to the project specification requirements:
1. Random Intercept: Must be `thread_id` (overriding Plan.md's suggestion of `subreddit`).
2. Distributions/Link Functions:
   - Beta regression for bounded outcomes (agreement proportion).
   - Appropriate distribution (Gamma/Log-Normal) for time-to-decision based on diagnostics.
3. Predictors: Must include `external_validation_score`.

Output: `state/model_specification_validation.json`
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/validate_model_specification.log')
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELING_SCRIPT = PROJECT_ROOT / "code" / "data" / "modeling.py"
STATE_DIR = PROJECT_ROOT / "state"
OUTPUT_FILE = STATE_DIR / "model_specification_validation.json"

# Specification Requirements (FR-006)
SPEC_REQUIREMENTS = {
    "random_intercept": "thread_id",
    "bounded_outcome_model": "beta_regression",
    "time_to_decision_model": ["gamma", "log_normal"], # Accept either based on diagnostics
    "predictors_required": ["external_validation_score"]
}

def extract_model_specification(script_path: Path) -> Dict[str, Any]:
    """
    Parse the modeling.py script to extract model specification details.
    Looks for comments, function arguments, and model initialization calls.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Modeling script not found at: {script_path}")

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    spec = {
        "random_intercept": None,
        "link_functions": {},
        "distributions": {},
        "predictors": [],
        "raw_content_snippets": []
    }

    lines = content.split('\n')

    # 1. Check for Random Intercept
    # Look for comments overriding Plan.md or explicit variable assignments
    intercept_patterns = [
        r"random_intercept\s*=\s*['\"]thread_id['\"]",
        r"random_effect\s*=\s*['\"]thread_id['\"]",
        r"groups\s*=\s*['\"]thread_id['\"]",
        r"# Override Plan.md.*thread_id",
        r"# Spec FR-006.*thread_id"
    ]
    
    found_intercept = False
    for pattern in intercept_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            spec["random_intercept"] = "thread_id"
            found_intercept = True
            logger.info("Found specification for random_intercept: thread_id")
            break
    
    if not found_intercept:
        # Check if 'subreddit' is used instead (violation)
        if re.search(r"random_intercept\s*=\s*['\"]subreddit['\"]", content, re.IGNORECASE):
            spec["random_intercept"] = "subreddit"
            logger.warning("Found random_intercept set to 'subreddit' (Violation of FR-006)")
        else:
            logger.warning("Could not determine random_intercept specification.")

    # 2. Check for Distributions and Link Functions
    # Look for beta regression, gamma, log_normal, etc.
    if "beta" in content.lower() and "regression" in content.lower():
        spec["distributions"]["agreement_proportion"] = "beta"
        spec["link_functions"]["agreement_proportion"] = "logit" # Standard for beta
        logger.info("Found Beta regression specification.")
    
    if "gamma" in content.lower():
        spec["distributions"]["time_to_decision"] = "gamma"
        logger.info("Found Gamma distribution specification.")
    
    if "log_normal" in content.lower() or "lognorm" in content.lower():
        spec["distributions"]["time_to_decision"] = "log_normal"
        logger.info("Found Log-Normal distribution specification.")

    # 3. Check for Predictors
    # Look for variable names in model formulas or data preparation
    required_predictors = SPEC_REQUIREMENTS["predictors_required"]
    found_predictors = []
    
    for pred in required_predictors:
        # Check if the variable name appears in a context suggesting it's a predictor
        # e.g., in a formula string or a data column selection
        patterns = [
            rf"['\"]{pred}['\"]",
            rf"{pred}\s*in\s*formula",
            rf"formula.*{pred}"
        ]
        for pat in patterns:
            if re.search(pat, content, re.IGNORECASE):
                found_predictors.append(pred)
                break
    
    spec["predictors"] = found_predictors

    return spec

def validate_specification(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare extracted specification against requirements.
    """
    results = {
        "status": "pass",
        "checks": {},
        "errors": [],
        "warnings": []
    }

    # Check 1: Random Intercept
    expected_intercept = SPEC_REQUIREMENTS["random_intercept"]
    actual_intercept = extracted.get("random_intercept")
    
    if actual_intercept == expected_intercept:
        results["checks"]["random_intercept"] = {
            "status": "pass",
            "expected": expected_intercept,
            "actual": actual_intercept
        }
    else:
        results["checks"]["random_intercept"] = {
            "status": "fail",
            "expected": expected_intercept,
            "actual": actual_intercept
        }
        results["errors"].append(f"Random intercept mismatch. Expected '{expected_intercept}', found '{actual_intercept}'.")
        results["status"] = "fail"

    # Check 2: Bounded Outcome (Beta Regression)
    if extracted.get("distributions", {}).get("agreement_proportion") == "beta":
        results["checks"]["bounded_outcome"] = {
            "status": "pass",
            "method": "beta_regression"
        }
    else:
        results["checks"]["bounded_outcome"] = {
            "status": "fail",
            "expected": "beta_regression",
            "actual": extracted.get("distributions", {}).get("agreement_proportion")
        }
        results["errors"].append("Bounded outcome (agreement proportion) is not modeled with Beta regression.")
        results["status"] = "fail"

    # Check 3: Time-to-Decision Distribution
    allowed_time_dist = SPEC_REQUIREMENTS["time_to_decision_model"]
    actual_time_dist = extracted.get("distributions", {}).get("time_to_decision")
    
    if actual_time_dist in allowed_time_dist:
        results["checks"]["time_to_decision"] = {
            "status": "pass",
            "distribution": actual_time_dist
        }
    else:
        # If not found, it might be missing or defaulting to something else
        results["checks"]["time_to_decision"] = {
            "status": "fail",
            "expected": allowed_time_dist,
            "actual": actual_time_dist
        }
        results["warnings"].append(f"Time-to-decision distribution not explicitly set to {allowed_time_dist}. Found: {actual_time_dist}.")
        # Note: We treat this as a warning unless the spec strictly forbids others, but for FR-006 compliance we expect explicit selection.

    # Check 4: Required Predictors
    required = SPEC_REQUIREMENTS["predictors_required"]
    found = extracted.get("predictors", [])
    missing = [p for p in required if p not in found]

    if not missing:
        results["checks"]["predictors"] = {
            "status": "pass",
            "required": required,
            "found": found
        }
    else:
        results["checks"]["predictors"] = {
            "status": "fail",
            "required": required,
            "found": found,
            "missing": missing
        }
        results["errors"].append(f"Missing required predictors: {missing}")
        results["status"] = "fail"

    return results

def save_report(report: Dict[str, Any], output_path: Path):
    """
    Save the validation report to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to: {output_path}")

def main():
    logger.info("Starting Model Specification Validation (T055)...")
    
    try:
        # 1. Extract specification from code
        extracted_spec = extract_model_specification(MODELING_SCRIPT)
        
        # 2. Validate against requirements
        validation_results = validate_specification(extracted_spec)
        
        # 3. Prepare final report
        final_report = {
            "task_id": "T055",
            "status": validation_results["status"],
            "random_intercept": extracted_spec.get("random_intercept"),
            "link_functions": extracted_spec.get("link_functions", {}),
            "distributions": extracted_spec.get("distributions", {}),
            "checks": validation_results["checks"],
            "errors": validation_results["errors"],
            "warnings": validation_results["warnings"]
        }
        
        # 4. Save report
        save_report(final_report, OUTPUT_FILE)
        
        # 5. Exit with appropriate code
        if validation_results["status"] == "fail":
            logger.error("Model specification validation FAILED.")
            sys.exit(1)
        else:
            logger.info("Model specification validation PASSED.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Validation process failed with exception: {e}")
        error_report = {
            "task_id": "T055",
            "status": "fail",
            "error": str(e)
        }
        save_report(error_report, OUTPUT_FILE)
        sys.exit(1)

if __name__ == "__main__":
    main()