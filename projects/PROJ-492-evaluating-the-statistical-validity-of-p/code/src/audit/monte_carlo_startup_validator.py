"""
Monte-Carlo Startup Validator (T031)

This module implements the startup validation step required by task T031.
It runs the Monte-Carlo validation (from T062) as part of the pipeline start-up
to ensure statistical methods are valid before processing real data.

Per Constitution Principle I (Reproducibility), this uses the global SEED
defined in code.src.config to ensure deterministic results.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED

# Error codes for startup validation
ERR_MC_STARTUP_001 = "ERR-501"  # Monte-Carlo validation failed
ERR_MC_STARTUP_002 = "ERR-502"  # Monte-Carlo validation timeout
ERR_MC_STARTUP_003 = "ERR-503"  # Monte-Carlo validation resource limit exceeded

# Thresholds
MC_VALIDATION_TIMEOUT_SECONDS = 300  # 5 minutes max for startup validation
MC_ACCEPTANCE_TOLERANCE = 0.005  # Absolute difference threshold for p-values


def run_startup_validation(
    output_dir: Optional[Path] = None,
    timeout_seconds: int = MC_VALIDATION_TIMEOUT_SECONDS,
    tolerance: float = MC_ACCEPTANCE_TOLERANCE,
    num_replicates: int = 10000,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run Monte-Carlo validation as part of pipeline start-up.

    This function:
    1. Initializes the logger
    2. Calls run_monte_carlo_validation from T062
    3. Validates that all statistical tests pass within tolerance
    4. Writes results to output/mc_startup_validation.json
    5. Returns success status and results dictionary

    Args:
        output_dir: Directory to write validation results. Defaults to 'output/'.
        timeout_seconds: Maximum time allowed for validation.
        tolerance: Maximum acceptable absolute difference for p-values.
        num_replicates: Number of Monte-Carlo replicates to run.

    Returns:
        Tuple of (success: bool, results: Dict)
        success is True if all tests pass within tolerance
        results contains detailed validation metrics
    """
    logger = get_default_logger(__name__)
    audit_logger = AuditLogger(logger)

    logger.info(f"Starting Monte-Carlo startup validation (T031) with {num_replicates} replicates")
    logger.info(f"Using global SEED: {SEED}")

    start_time = time.time()

    try:
        # Run the Monte-Carlo validation from T062
        results = run_monte_carlo_validation(
            output_dir=output_dir,
            num_replicates=num_replicates,
            tolerance=tolerance,
        )

        elapsed_time = time.time() - start_time

        # Check if validation completed within timeout
        if elapsed_time > timeout_seconds:
            error_msg = get_error_message(ERR_MC_STARTUP_002)
            logger.error(f"{ERR_MC_STARTUP_002}: Validation took {elapsed_time:.2f}s, exceeded {timeout_seconds}s limit")
            audit_logger.log_error(ERR_MC_STARTUP_002, f"Validation timeout: {elapsed_time:.2f}s")
            return False, {
                "status": "timeout",
                "elapsed_time": elapsed_time,
                "timeout_seconds": timeout_seconds,
                "results": results,
            }

        # Check if all tests passed
        all_passed = True
        failed_tests = []

        for test_name, test_result in results.get("test_results", {}).items():
            if not test_result.get("passed", False):
                all_passed = False
                failed_tests.append({
                    "test": test_name,
                    "expected_p": test_result.get("expected_p_value"),
                    "observed_p": test_result.get("observed_p_value"),
                    "difference": test_result.get("difference"),
                    "tolerance": tolerance,
                })

        if not all_passed:
            error_msg = get_error_message(ERR_MC_STARTUP_001)
            logger.error(f"{ERR_MC_STARTUP_001}: {len(failed_tests)} test(s) failed validation")
            for failed in failed_tests:
                logger.error(f"  - {failed['test']}: diff={failed['difference']:.6f} > tol={tolerance}")
            audit_logger.log_error(ERR_MC_STARTUP_001, f"{len(failed_tests)} tests failed")

        # Write summary to output file
        if output_dir:
            output_path = Path(output_dir) / "mc_startup_validation.json"
            summary = {
                "status": "passed" if all_passed else "failed",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "seed": SEED,
                "num_replicates": num_replicates,
                "tolerance": tolerance,
                "elapsed_time": elapsed_time,
                "timeout_seconds": timeout_seconds,
                "all_tests_passed": all_passed,
                "failed_tests": failed_tests,
                "test_results": results.get("test_results", {}),
            }

            import json
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Startup validation results written to {output_path}")

        return all_passed, {
            "status": "passed" if all_passed else "failed",
            "elapsed_time": elapsed_time,
            "timeout_seconds": timeout_seconds,
            "num_replicates": num_replicates,
            "tolerance": tolerance,
            "all_tests_passed": all_passed,
            "failed_tests": failed_tests,
            "test_results": results.get("test_results", {}),
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.exception(f"Exception during Monte-Carlo startup validation: {e}")
        audit_logger.log_error(ERR_MC_STARTUP_001, f"Validation exception: {str(e)}")
        return False, {
            "status": "error",
            "elapsed_time": elapsed_time,
            "error": str(e),
            "exception_type": type(e).__name__,
        }


def main() -> int:
    """
    Main entry point for Monte-Carlo startup validation script.

    This is the CLI entry point that can be called directly or from the pipeline.
    Returns 0 on success, 1 on failure.
    """
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Run Monte-Carlo validation at pipeline start-up (T031)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write validation results (default: output/)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=MC_VALIDATION_TIMEOUT_SECONDS,
        help=f"Timeout in seconds (default: {MC_VALIDATION_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=MC_ACCEPTANCE_TOLERANCE,
        help=f"P-value tolerance (default: {MC_ACCEPTANCE_TOLERANCE})",
    )
    parser.add_argument(
        "--replicates",
        type=int,
        default=10000,
        help="Number of Monte-Carlo replicates (default: 10000)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    success, results = run_startup_validation(
        output_dir=args.output_dir,
        timeout_seconds=args.timeout,
        tolerance=args.tolerance,
        num_replicates=args.replicates,
    )

    if success:
        print(f"Monte-Carlo startup validation PASSED ({results['elapsed_time']:.2f}s)")
        return 0
    else:
        status = results.get("status", "unknown")
        if status == "error":
            print(f"Monte-Carlo startup validation FAILED with error: {results.get('error')}")
        elif status == "timeout":
            print(f"Monte-Carlo startup validation FAILED: timeout ({results['elapsed_time']:.2f}s)")
        else:
            print(f"Monte-Carlo startup validation FAILED: {len(results.get('failed_tests', []))} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())