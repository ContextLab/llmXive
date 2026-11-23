import os
import sys
import time
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Define the sequence of scripts that constitute the full pipeline
PIPELINE_STAGES = [
    "code/data/download.py",
    "code/data/descriptors.py",
    "code/data/preprocess.py",
    "code/models/train.py",
    "code/models/predict.py",
    "code/models/generate_candidates_report.py",
]

MAX_RUNTIME_HOURS = 6
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

def run_pipeline_script(script_rel_path: str, timeout_seconds: Optional[int] = None) -> Tuple[bool, float, str]:
    """
    Executes a single pipeline script and returns execution status, duration, and output.
    
    Args:
        script_rel_path: Relative path from project root to the script.
        timeout_seconds: Optional timeout in seconds.
        
    Returns:
        Tuple of (success, duration_seconds, output_log)
    """
    script_path = Path(script_rel_path)
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False, 0.0, f"Script not found: {script_path}"

    logger.info(f"Starting stage: {script_rel_path}")
    start_time = time.time()
    
    try:
        cmd = [sys.executable, str(script_path)]
        env = os.environ.copy()
        
        # Run the script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env
        )
        
        duration = time.time() - start_time
        output = result.stdout + "\n" + result.stderr
        
        if result.returncode != 0:
            logger.error(f"Stage failed: {script_rel_path} (Exit code: {result.returncode})")
            logger.error(f"Output: {output}")
            return False, duration, output
        
        logger.info(f"Stage completed: {script_rel_path} in {duration:.2f}s")
        return True, duration, output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Stage timed out: {script_rel_path}")
        return False, duration, f"Timeout after {timeout_seconds}s"
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Stage exception: {script_rel_path} - {str(e)}")
        return False, duration, str(e)

def run_full_pipeline_validation(output_path: str = "results/pipeline_timing_report.txt") -> bool:
    """
    Runs the full pipeline sequentially, measures total time, and writes a validation report.
    
    Args:
        output_path: Path to save the timing report.
        
    Returns:
        True if total runtime <= MAX_RUNTIME_HOURS, False otherwise.
    """
    logger.info("Starting full pipeline timing validation...")
    
    total_start = time.time()
    stage_results = []
    all_passed = True

    for stage in PIPELINE_STAGES:
        success, duration, output = run_pipeline_script(stage)
        stage_results.append({
            "stage": stage,
            "success": success,
            "duration_seconds": duration
        })
        
        if not success:
            all_passed = False
            logger.error(f"Pipeline aborted at stage: {stage}")
            break

    total_duration = time.time() - total_start
    
    # Determine pass/fail based on time constraint
    passed_time_check = total_duration <= MAX_RUNTIME_SECONDS
    
    # Generate report
    report_lines = [
        "=" * 60,
        "PIPELINE TIMING VALIDATION REPORT",
        "=" * 60,
        f"Max Allowed Runtime: {MAX_RUNTIME_HOURS} hours ({MAX_RUNTIME_SECONDS} seconds)",
        f"Total Actual Runtime: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)",
        f"Time Constraint Met: {'PASS' if passed_time_check else 'FAIL'}",
        "-" * 60,
        "Stage Breakdown:",
        "-" * 60,
    ]

    for res in stage_results:
        status = "OK" if res["success"] else "FAILED"
        report_lines.append(
            f"{res['stage']}: {status} ({res['duration_seconds']:.2f}s)"
        )

    report_lines.append("-" * 60)
    report_lines.append(f"Overall Result: {'PASS' if (all_passed and passed_time_check) else 'FAIL'}")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    logger.info(report_text)

    # Ensure results directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report_text)

    logger.info(f"Timing report saved to {output_path}")
    
    return all_passed and passed_time_check

def main():
    """Entry point for running the timing validation."""
    parser = argparse.ArgumentParser(description="Verify total pipeline runtime <= 6 hours")
    parser.add_argument(
        "--output", 
        type=str, 
        default="results/pipeline_timing_report.txt",
        help="Path to save the timing report"
    )
    args = parser.parse_args()

    success = run_full_pipeline_validation(output_path=args.output)
    
    if success:
        logger.info("SUCCESS: Pipeline runtime is within the 6-hour limit.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Pipeline runtime exceeded 6 hours or a stage failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
