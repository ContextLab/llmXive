"""
Validation module for Success Criteria (SC) assertions.
Implements checks for SC-001 through SC-011 and writes validation_status.json.
"""
import json
import time
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants
VALIDATION_STATUS_PATH = Path("data/results/validation_status.json")
START_TIME_KEY = "start_time"
END_TIME_KEY = "end_time"

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None

def validate_retention_rate(summary_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-001: Validate retention rate >= 95%.
    """
    result = {"criterion": "SC-001", "description": "Retention Rate >= 95%", "status": "FAIL", "details": ""}
    
    if summary_report is None:
        result["details"] = "summary_report.json not found"
        return result

    retention_rate = summary_report.get("retention_rate")
    if retention_rate is None:
        result["details"] = "retention_rate field missing in summary_report"
        return result

    if retention_rate >= 0.95:
        result["status"] = "PASS"
        result["details"] = f"Retention rate {retention_rate:.2%} meets threshold"
    else:
        result["details"] = f"Retention rate {retention_rate:.2%} is below 95% threshold"
    
    return result

def validate_model_count(model_comparison: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-002: Validate at least 3 models converged.
    """
    result = {"criterion": "SC-002", "description": "At least 3 models converged", "status": "FAIL", "details": ""}
    
    if model_comparison is None:
        result["details"] = "model_comparison.json not found"
        return result

    models = model_comparison.get("models", [])
    converged_count = sum(1 for m in models if m.get("converged", False))
    
    if converged_count >= 3:
        result["status"] = "PASS"
        result["details"] = f"{converged_count} models converged"
    else:
        result["details"] = f"Only {converged_count} models converged (need >= 3)"
    
    return result

def validate_hill_index(tail_index_estimate: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-003: Validate Hill index estimation was performed and is positive.
    """
    result = {"criterion": "SC-003", "description": "Hill index estimated and positive", "status": "FAIL", "details": ""}
    
    if tail_index_estimate is None:
        result["details"] = "tail_index_estimate.json not found"
        return result

    tail_index = tail_index_estimate.get("tail_index")
    if tail_index is None:
        result["details"] = "tail_index field missing"
        return result

    if tail_index > 0:
        result["status"] = "PASS"
        result["details"] = f"Hill index estimated at {tail_index:.4f}"
    else:
        result["details"] = f"Hill index {tail_index} is not positive"
    
    return result

def validate_r2_visualization(r2_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-004: Validate R^2 >= 0.95 for visualization reporting.
    NOTE: This is for reporting only, not a pass/fail gate for the pipeline.
    """
    result = {"criterion": "SC-004", "description": "R² >= 0.95 (Visualization Reporting Only)", "status": "REPORT", "details": ""}
    
    if r2_results is None:
        result["details"] = "r2_results.json not found"
        return result

    r2_value = r2_results.get("r2_value")
    if r2_value is None:
        result["details"] = "r2_value field missing"
        return result

    if r2_value >= 0.95:
        result["status"] = "PASS"
        result["details"] = f"R² = {r2_value:.4f} meets visualization threshold"
    else:
        result["status"] = "REPORT" # Still report, but note it's below threshold
        result["details"] = f"R² = {r2_value:.4f} is below 0.95 (for visualization only)"
    
    return result

def validate_runtime(start_time: float, end_time: float) -> Dict[str, Any]:
    """
    SC-005: Validate runtime <= 3600s.
    """
    result = {"criterion": "SC-005", "description": "Runtime <= 3600s", "status": "FAIL", "details": ""}
    
    elapsed = end_time - start_time
    if elapsed <= 3600:
        result["status"] = "PASS"
        result["details"] = f"Runtime {elapsed:.2f}s is within 3600s limit"
    else:
        result["details"] = f"Runtime {elapsed:.2f}s exceeds 3600s limit"
    
    return result

def validate_vuong_test(vuong_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-006: Validate Vuong test was performed and p-value is present.
    """
    result = {"criterion": "SC-006", "description": "Vuong test performed with p-value", "status": "FAIL", "details": ""}
    
    if vuong_results is None:
        result["details"] = "vuong_test_results.json not found"
        return result

    p_value = vuong_results.get("p_value")
    if p_value is not None:
        result["status"] = "PASS"
        result["details"] = f"Vuong test p-value: {p_value:.4f}"
    else:
        result["details"] = "p_value field missing in vuong_test_results"
    
    return result

def validate_tail_ks(tail_ks_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-007: Validate Tail KS test was performed and p-value is present.
    """
    result = {"criterion": "SC-007", "description": "Tail KS test performed with p-value", "status": "FAIL", "details": ""}
    
    if tail_ks_results is None:
        result["details"] = "tail_ks.json not found"
        return result

    p_value = tail_ks_results.get("p_value")
    if p_value is not None:
        result["status"] = "PASS"
        result["details"] = f"Tail KS test p-value: {p_value:.4f}"
    else:
        result["details"] = "p_value field missing in tail_ks results"
    
    return result

def validate_stability_window(stability_curve: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-009: Validate stability window analysis was performed.
    """
    result = {"criterion": "SC-009", "description": "Stability window analysis performed", "status": "FAIL", "details": ""}
    
    if stability_curve is None:
        # Check if the file exists but couldn't be loaded, or if it's missing entirely
        result["details"] = "stability_curve.csv or stability data not found"
        return result

    # If we have data, we assume the analysis was performed
    result["status"] = "PASS"
    result["details"] = "Stability window analysis completed"
    
    return result

def validate_pvalues(vuong_results: Optional[Dict[str, Any]], tail_ks_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SC-010/SC-011: Validate p-values are in valid range [0, 1].
    """
    result = {"criterion": "SC-010/SC-011", "description": "P-values in valid range [0, 1]", "status": "FAIL", "details": ""}
    
    issues = []
    
    if vuong_results:
        p_vuong = vuong_results.get("p_value")
        if p_vuong is not None and not (0 <= p_vuong <= 1):
            issues.append(f"Vuong p-value {p_vuong} out of range")
    
    if tail_ks_results:
        p_ks = tail_ks_results.get("p_value")
        if p_ks is not None and not (0 <= p_ks <= 1):
            issues.append(f"Tail KS p-value {p_ks} out of range")
    
    if not issues:
        result["status"] = "PASS"
        result["details"] = "All p-values are within valid range [0, 1]"
    else:
        result["details"] = "; ".join(issues)
    
    return result

def run_validation(start_time: float, end_time: float) -> Dict[str, Any]:
    """
    Run all validation checks and compile results.
    """
    logger.info("Starting validation of success criteria...")
    
    # Load all required result files
    summary_report = load_json_safe(Path("data/processed/summary_report.json"))
    model_comparison = load_json_safe(Path("data/results/model_comparison.json"))
    tail_index_estimate = load_json_safe(Path("data/results/tail_index_estimate.json"))
    r2_results = load_json_safe(Path("data/results/r2_results.json"))
    vuong_results = load_json_safe(Path("data/results/vuong_test_results.json"))
    tail_ks_results = load_json_safe(Path("data/results/tail_ks.json"))
    stability_curve = load_json_safe(Path("data/results/stability_curve.json")) # Assuming JSON wrapper for CSV or direct JSON
    
    # Run individual validations
    validations = [
        validate_retention_rate(summary_report),
        validate_model_count(model_comparison),
        validate_hill_index(tail_index_estimate),
        validate_r2_visualization(r2_results),
        validate_runtime(start_time, end_time),
        validate_vuong_test(vuong_results),
        validate_tail_ks(tail_ks_results),
        validate_stability_window(stability_curve),
        validate_pvalues(vuong_results, tail_ks_results)
    ]
    
    # Compile final status
    status_summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": end_time - start_time,
        "criteria_results": validations,
        "overall_status": "PASS" if all(v["status"] == "PASS" or v["status"] == "REPORT" for v in validations) else "FAIL"
    }
    
    # Check for any FAIL status (excluding REPORT)
    if any(v["status"] == "FAIL" for v in validations):
        status_summary["overall_status"] = "FAIL"
    
    # Save results
    VALIDATION_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_STATUS_PATH, 'w') as f:
        json.dump(status_summary, f, indent=2)
    
    logger.info(f"Validation complete. Results saved to {VALIDATION_STATUS_PATH}")
    return status_summary

def main():
    """Entry point for validation script."""
    # Get start and end times from environment or command line args if needed
    # For now, assume they are passed or we use current time for runtime check
    # In a real pipeline, these would be injected by the orchestrator
    start_time = float(sys.argv[1]) if len(sys.argv) > 1 else time.time()
    end_time = float(sys.argv[2]) if len(sys.argv) > 2 else time.time()
    
    run_validation(start_time, end_time)

if __name__ == "__main__":
    main()
