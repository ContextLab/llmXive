"""
Batch validation script.
Verifies SC-001 (target count), SC-002 (runtime), and SC-005 (sensitivity thresholds).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def validate_sc_001(manifest_path: str, expected_count: Optional[int] = None) -> Dict[str, Any]:
    """
    Validate SC-001: Configured target count is met.
    Checks global_batch_manifest.json for valid_count.
    """
    result = {"status": "FAIL", "details": {}}
    
    p = Path(manifest_path)
    if not p.exists():
        result["details"]["error"] = "Manifest not found"
        return result
        
    with open(p, 'r') as f:
        manifest = json.load(f)
        
    valid_count = manifest.get("summary", {}).get("valid_count", 0)
    result["details"]["valid_count"] = valid_count
    
    if expected_count and valid_count < expected_count:
        result["details"]["reason"] = f"Valid count {valid_count} < expected {expected_count}"
        return result
        
    result["status"] = "PASS"
    return result

def validate_sc_002(simulation_results_path: str, max_runtime_seconds: float = 3600) -> Dict[str, Any]:
    """
    Validate SC-002: Runtime per network <= 60 minutes (3600 seconds).
    Checks runtime_duration_seconds field in simulation_results.json.
    """
    result = {"status": "PASS", "details": {"max_runtime_found": 0, "violations": 0}}
    
    p = Path(simulation_results_path)
    if not p.exists():
        result["status"] = "FAIL"
        result["details"]["error"] = "Simulation results not found"
        return result
        
    with open(p, 'r') as f:
        data = json.load(f)
        
    records = data if isinstance(data, list) else data.get("results", [])
    
    max_runtime = 0
    violations = 0
    for r in records:
        runtime = r.get("runtime_duration_seconds", 0)
        if runtime > max_runtime:
            max_runtime = runtime
        if runtime > max_runtime_seconds:
            violations += 1
            
    result["details"]["max_runtime_found"] = max_runtime
    result["details"]["violations"] = violations
    
    if violations > 0:
        result["status"] = "FAIL"
        
    return result

def validate_sc_005(sensitivity_path: str, min_thresholds: int = 5) -> Dict[str, Any]:
    """
    Validate SC-005: Sensitivity sweep has >= 5 distinct cutoffs.
    Checks sensitivity_sweep.json for distinct thresholds.
    """
    result = {"status": "FAIL", "details": {}}
    
    p = Path(sensitivity_path)
    if not p.exists():
        result["details"]["error"] = "Sensitivity sweep file not found"
        return result
        
    with open(p, 'r') as f:
        data = json.load(f)
        
    thresholds = data.get("sweep_parameters", {}).get("thresholds", [])
    distinct_count = len(set(thresholds))
    
    result["details"]["thresholds_found"] = thresholds
    result["details"]["distinct_count"] = distinct_count
    
    if distinct_count >= min_thresholds:
        result["status"] = "PASS"
    else:
        result["details"]["reason"] = f"Only {distinct_count} distinct thresholds, need {min_thresholds}"
        
    return result

def generate_validation_report(sc_001: Dict, sc_002: Dict, sc_005: Dict, output_path: str) -> None:
    """Generate the final validation report."""
    report = {
        "sc_001_status": sc_001.get("status", "FAIL"),
        "sc_002_status": sc_002.get("status", "FAIL"),
        "sc_005_status": sc_005.get("status", "FAIL"),
        "details": {
            "sc_001": sc_001.get("details", {}),
            "sc_002": sc_002.get("details", {}),
            "sc_005": sc_005.get("details", {})
        },
        "overall_status": "PASS" if all(s.get("status") == "PASS" for s in [sc_001, sc_002, sc_005]) else "FAIL"
    }
    
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for batch validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate batch results")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = Path(args.output)
    manifest_path = output_path / "raw" / "global_batch_manifest.json"
    simulation_path = output_path / "analysis" / "simulation_results.json"
    sensitivity_path = output_path / "analysis" / "sensitivity_sweep.json"
    report_path = output_path / "analysis" / "validation_report.json"
    
    # Run validations
    sc_001 = validate_sc_001(str(manifest_path))
    sc_002 = validate_sc_002(str(simulation_path))
    sc_005 = validate_sc_005(str(sensitivity_path))
    
    # Generate report
    generate_validation_report(sc_001, sc_002, sc_005, str(report_path))
    
    if sc_001["status"] == "PASS" and sc_002["status"] == "PASS" and sc_005["status"] == "PASS":
        logger.info("All validations PASSED")
    else:
        logger.warning("Some validations FAILED")

if __name__ == "__main__":
    main()