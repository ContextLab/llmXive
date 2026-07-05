"""
Pipeline timing and validation utilities for Task T042.

Verifies total pipeline runtime is within the 6-hour constraint.
"""
import os
import sys
import time
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
PIPELINE_SCRIPTS = [
    "code/data/download.py",
    "code/data/descriptors.py",
    "code/data/preprocess.py",
    "code/models/train.py",
    "code/models/predict.py",
    "code/models/generate_candidates_report.py",
    "code/viz/plot.py",
]

def run_pipeline_script(script_rel_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute a single pipeline script and measure its runtime.
    
    Args:
        script_rel_path: Relative path to the script from project root.
        dry_run: If True, only log what would be run without executing.
        
    Returns:
        Dictionary with execution status and timing information.
    """
    script_path = project_root / script_rel_path
    
    if not script_path.exists():
        logger.warning(f"Script not found: {script_path}")
        return {
            "script": script_rel_path,
            "status": "skipped",
            "reason": "file_not_found",
            "runtime_seconds": 0,
        }

    logger.info(f"Executing: {script_rel_path}")
    
    if dry_run:
        logger.info(f"DRY RUN: Would execute python {script_path}")
        return {
            "script": script_rel_path,
            "status": "dry_run",
            "runtime_seconds": 0,
        }

    start_time = time.time()
    try:
        # Run the script with timeout protection (e.g., 7 hours per script max)
        timeout_seconds = 7 * 60 * 60
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        
        runtime = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"Completed {script_rel_path} in {runtime:.2f}s")
            return {
                "script": script_rel_path,
                "status": "success",
                "runtime_seconds": runtime,
                "stdout_lines": len(result.stdout.splitlines()),
                "stderr_lines": len(result.stderr.splitlines()),
            }
        else:
            logger.error(f"Failed {script_rel_path} with return code {result.returncode}")
            logger.error(f"Stderr: {result.stderr[:500]}")
            return {
                "script": script_rel_path,
                "status": "failed",
                "runtime_seconds": runtime,
                "return_code": result.returncode,
                "error": result.stderr[:500],
            }
            
    except subprocess.TimeoutExpired:
        runtime = time.time() - start_time
        logger.error(f"Timeout expired for {script_rel_path} after {timeout_seconds}s")
        return {
            "script": script_rel_path,
            "status": "timeout",
            "runtime_seconds": runtime,
            "reason": f"exceeded {timeout_seconds}s limit",
        }
    except Exception as e:
        runtime = time.time() - start_time
        logger.error(f"Exception running {script_rel_path}: {str(e)}")
        return {
            "script": script_rel_path,
            "status": "error",
            "runtime_seconds": runtime,
            "error": str(e),
        }

def run_full_pipeline_validation(dry_run: bool = False) -> Dict[str, Any]:
    """
    Run the full pipeline validation to measure total runtime.
    
    Args:
        dry_run: If True, simulate execution without running scripts.
        
    Returns:
        Summary dictionary with total runtime and status.
    """
    logger.info("Starting pipeline runtime validation")
    log_pipeline_event("T042_START", "Beginning pipeline runtime verification")
    
    results = []
    total_runtime = 0.0
    failed_scripts = []
    
    for script in PIPELINE_SCRIPTS:
        result = run_pipeline_script(script, dry_run=dry_run)
        results.append(result)
        
        if result["status"] in ["success", "dry_run"]:
            total_runtime += result.get("runtime_seconds", 0)
        elif result["status"] in ["failed", "timeout", "error"]:
            failed_scripts.append(script)
    
    total_runtime_hours = total_runtime / 3600.0
    passed = total_runtime <= MAX_RUNTIME_SECONDS and len(failed_scripts) == 0
    
    summary = {
        "total_runtime_seconds": total_runtime,
        "total_runtime_hours": total_runtime_hours,
        "max_allowed_hours": 6.0,
        "passed": passed,
        "script_count": len(PIPELINE_SCRIPTS),
        "success_count": len([r for r in results if r["status"] == "success"]),
        "failed_scripts": failed_scripts,
        "results": results,
    }
    
    # Log summary
    log_pipeline_event(
        "T042_SUMMARY",
        f"Pipeline validation: {total_runtime_hours:.2f}h / 6h limit. "
        f"Passed: {passed}. Failed scripts: {len(failed_scripts)}"
    )
    
    if passed:
        logger.info(f"✅ PIPELINE VALIDATION PASSED: {total_runtime_hours:.2f} hours <= 6 hours")
    else:
        logger.error(f"❌ PIPELINE VALIDATION FAILED: {total_runtime_hours:.2f} hours > 6 hours or {len(failed_scripts)} failures")
        
    return summary

def main():
    """Main entry point for pipeline timing verification."""
    parser = argparse.ArgumentParser(
        description="Verify total pipeline runtime is within 6 hours."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without running scripts."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    summary = run_full_pipeline_validation(dry_run=args.dry_run)
    
    # Print summary to stdout for easy parsing
    print("\n" + "="*60)
    print("PIPELINE RUNTIME VALIDATION REPORT")
    print("="*60)
    print(f"Total Runtime: {summary['total_runtime_hours']:.2f} hours")
    print(f"Allowed Limit: {summary['max_allowed_hours']} hours")
    print(f"Status: {'PASSED' if summary['passed'] else 'FAILED'}")
    print(f"Scripts Executed: {summary['success_count']}/{summary['script_count']}")
    
    if summary['failed_scripts']:
        print(f"Failed Scripts: {', '.join(summary['failed_scripts'])}")
    
    print("="*60)
    
    # Return exit code based on validation result
    if summary['passed']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
