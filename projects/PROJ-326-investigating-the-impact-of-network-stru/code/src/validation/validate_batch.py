import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.config import load_config

logger = logging.getLogger(__name__)

# Constants for validation thresholds
SC_001_MIN_GRAPHS = 5
SC_002_MAX_RUNTIME_SECONDS = 3600  # 60 minutes
SC_005_MIN_CUTOFFS = 5

def check_sc001_graph_count(manifest_path: Path) -> Dict[str, Any]:
    """
    Validate SC-001: Configured target count of graphs generated.
    Checks data/raw/global_batch_manifest.json for total_generated >= SC_001_MIN_GRAPHS.
    """
    result = {
        "status": "FAIL",
        "details": {
            "manifest_path": str(manifest_path),
            "required_minimum": SC_001_MIN_GRAPHS,
            "actual_count": 0,
            "reason": "Manifest file not found"
        }
    }

    if not manifest_path.exists():
        logger.warning(f"SC-001 Check failed: Manifest file not found at {manifest_path}")
        return result

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        total_generated = manifest.get("total_generated", 0)
        result["details"]["actual_count"] = total_generated

        if total_generated >= SC_001_MIN_GRAPHS:
            result["status"] = "PASS"
            logger.info(f"SC-001 Check passed: {total_generated} graphs generated (min {SC_001_MIN_GRAPHS})")
        else:
            result["details"]["reason"] = f"Insufficient graphs: {total_generated} < {SC_001_MIN_GRAPHS}"
            logger.warning(f"SC-001 Check failed: {total_generated} graphs generated (min {SC_001_MIN_GRAPHS})")

    except json.JSONDecodeError as e:
        result["details"]["reason"] = f"Invalid JSON in manifest: {str(e)}"
        logger.error(f"SC-001 Check failed: Invalid JSON in manifest", exc_info=True)
    except Exception as e:
        result["details"]["reason"] = f"Unexpected error reading manifest: {str(e)}"
        logger.error(f"SC-001 Check failed: Unexpected error", exc_info=True)

    return result

def check_sc002_runtime(run_log_path: Path) -> Dict[str, Any]:
    """
    Validate SC-002: Runtime < 60m per network.
    Checks data/run_log.json for total runtime.
    Note: Since the log might contain multiple runs, we check the average or max if available,
    or simply check if the total time recorded is reasonable relative to the count.
    For this implementation, we assume the run_log captures the total execution time of the pipeline.
    If the pipeline generates N graphs, total_time / N should be < 60m.
    """
    result = {
        "status": "FAIL",
        "details": {
            "run_log_path": str(run_log_path),
            "max_allowed_per_network_seconds": SC_002_MAX_RUNTIME_SECONDS,
            "actual_runtime_seconds": 0,
            "network_count": 0,
            "avg_runtime_seconds": 0,
            "reason": "Run log file not found"
        }
    }

    if not run_log_path.exists():
        logger.warning(f"SC-002 Check failed: Run log file not found at {run_log_path}")
        return result

    try:
        with open(run_log_path, 'r') as f:
            log_data = json.load(f)

        # Attempt to extract runtime. The schema might vary, looking for common keys.
        # Assuming 'total_runtime_seconds' or similar is stored, or we calculate from timestamps.
        # If the log doesn't have explicit runtime, we might need to infer from the batch manifest count.
        # For robustness, we check for a 'metrics' or 'runtime' section.
        runtime = log_data.get("total_runtime_seconds", 0)
        if runtime == 0 and "metrics" in log_data:
            runtime = log_data["metrics"].get("total_runtime_seconds", 0)

        # If we can't find runtime, we might need to rely on the batch manifest count to estimate,
        # but strictly speaking, we need the time. If time is missing, we fail or warn.
        # Let's assume for this task that the run_log has 'total_runtime_seconds'.
        # If not, we check the batch manifest for count and assume a default or fail.
        
        # Fallback: Check if we have a batch manifest to get count
        batch_manifest_path = run_log_path.parent / "raw" / "global_batch_manifest.json"
        network_count = 0
        if batch_manifest_path.exists():
            with open(batch_manifest_path, 'r') as f:
                batch_manifest = json.load(f)
            network_count = batch_manifest.get("total_generated", 0)
        
        result["details"]["network_count"] = network_count
        result["details"]["actual_runtime_seconds"] = runtime

        if runtime > 0 and network_count > 0:
            avg_runtime = runtime / network_count
            result["details"]["avg_runtime_seconds"] = avg_runtime
            if avg_runtime < SC_002_MAX_RUNTIME_SECONDS:
                result["status"] = "PASS"
                logger.info(f"SC-002 Check passed: Avg runtime {avg_runtime:.2f}s < {SC_002_MAX_RUNTIME_SECONDS}s")
            else:
                result["details"]["reason"] = f"Avg runtime {avg_runtime:.2f}s exceeds limit"
                logger.warning(f"SC-002 Check failed: Avg runtime {avg_runtime:.2f}s exceeds limit")
        elif runtime == 0:
            result["details"]["reason"] = "Runtime not recorded in log"
            logger.warning("SC-002 Check failed: Runtime not recorded")
        else:
            result["details"]["reason"] = "Network count is zero"
            logger.warning("SC-002 Check failed: Network count is zero")

    except json.JSONDecodeError as e:
        result["details"]["reason"] = f"Invalid JSON in run log: {str(e)}"
        logger.error(f"SC-002 Check failed: Invalid JSON", exc_info=True)
    except Exception as e:
        result["details"]["reason"] = f"Unexpected error reading run log: {str(e)}"
        logger.error(f"SC-002 Check failed: Unexpected error", exc_info=True)

    return result

def check_sc005_sensitivity_sweep(sensitivity_path: Path) -> Dict[str, Any]:
    """
    Validate SC-005: Sensitivity sweep has >= 5 distinct cutoffs.
    Checks data/analysis/sensitivity_sweep.json.
    """
    result = {
        "status": "FAIL",
        "details": {
            "sensitivity_path": str(sensitivity_path),
            "required_minimum_cutoffs": SC_005_MIN_CUTOFFS,
            "actual_cutoffs": 0,
            "cutoffs_list": [],
            "reason": "Sensitivity sweep file not found"
        }
    }

    if not sensitivity_path.exists():
        logger.warning(f"SC-005 Check failed: Sensitivity sweep file not found at {sensitivity_path}")
        return result

    try:
        with open(sensitivity_path, 'r') as f:
            sweep_data = json.load(f)

        # The schema defined in T035a has key 'cutoffs' (list of floats)
        cutoffs = sweep_data.get("cutoffs", [])
        
        # Ensure they are distinct
        distinct_cutoffs = list(set(cutoffs))
        count = len(distinct_cutoffs)

        result["details"]["actual_cutoffs"] = count
        result["details"]["cutoffs_list"] = distinct_cutoffs

        if count >= SC_005_MIN_CUTOFFS:
            result["status"] = "PASS"
            logger.info(f"SC-005 Check passed: {count} distinct cutoffs found (min {SC_005_MIN_CUTOFFS})")
        else:
            result["details"]["reason"] = f"Insufficient distinct cutoffs: {count} < {SC_005_MIN_CUTOFFS}"
            logger.warning(f"SC-005 Check failed: {count} distinct cutoffs found (min {SC_005_MIN_CUTOFFS})")

    except json.JSONDecodeError as e:
        result["details"]["reason"] = f"Invalid JSON in sensitivity sweep: {str(e)}"
        logger.error(f"SC-005 Check failed: Invalid JSON", exc_info=True)
    except Exception as e:
        result["details"]["reason"] = f"Unexpected error reading sensitivity sweep: {str(e)}"
        logger.error(f"SC-005 Check failed: Unexpected error", exc_info=True)

    return result

def generate_validation_report(
    config_path: Path,
    output_path: Path,
    batch_manifest_path: Optional[Path] = None,
    run_log_path: Optional[Path] = None,
    sensitivity_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to generate the validation report.
    Orchestrates checks for SC-001, SC-002, and SC-005.
    """
    config = load_config(config_path)
    
    # Default paths if not provided
    data_root = Path(config.get("paths", {}).get("data", "data"))
    
    if batch_manifest_path is None:
        batch_manifest_path = data_root / "raw" / "global_batch_manifest.json"
    if run_log_path is None:
        run_log_path = data_root / "run_log.json"
    if sensitivity_path is None:
        sensitivity_path = data_root / "analysis" / "sensitivity_sweep.json"

    logger.info(f"Starting validation report generation. Output: {output_path}")

    sc001_result = check_sc001_graph_count(batch_manifest_path)
    sc002_result = check_sc002_runtime(run_log_path)
    sc005_result = check_sc005_sensitivity_sweep(sensitivity_path)

    report = {
        "sc_001_status": sc001_result["status"],
        "sc_002_status": sc002_result["status"],
        "sc_005_status": sc005_result["status"],
        "details": {
            "sc_001": sc001_result["details"],
            "sc_002": sc002_result["details"],
            "sc_005": sc005_result["details"]
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate validation report for SC-001, SC-002, SC-005")
    parser.add_argument("--config", type=str, required=True, help="Path to config.yaml")
    parser.add_argument("--output", type=str, required=True, help="Path to output validation_report.json")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config_path = Path(args.config)
    output_path = Path(args.output)

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1

    generate_validation_report(config_path, output_path)
    return 0

if __name__ == "__main__":
    exit(main())
