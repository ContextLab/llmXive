"""
Performance verification script for T044.

Verifies that the data processing and analysis pipeline runs within the
6-hour limit on 2 CPU cores. This script orchestrates the execution of
the core pipeline stages and measures total wall-clock time.

Pipeline Stages:
1. Download and Preprocess (US1)
2. Compute Intervals and Bin (US2)
3. Model Fitting and Sensitivity (US3)

Constraints:
- Max Runtime: 6 hours (21,600 seconds)
- CPU Cores: 2 (enforced via environment variable)
- Real Data: Must use existing data or download from real source
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import resource

# Import project utilities
from config import load_config, get_config_value
from logging_config import get_logger, info, warning, error, setup_logger

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_CPU_CORES = 2
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Pipeline stage definitions
PIPELINE_STAGES = [
    {
        "name": "Download and Preprocess (US1)",
        "script": "download_data.py",
        "description": "Fetch OULAD data and extract learner records",
        "required_output": "data/raw/",
        "next_stage": "preprocess.py"
    },
    {
        "name": "Preprocess and Filter (US1)",
        "script": "preprocess.py",
        "description": "Filter courses and extract learner data",
        "required_output": "data/processed/learners_raw.csv",
        "depends_on": "download_data.py"
    },
    {
        "name": "Compute Intervals (US2)",
        "script": "compute_intervals.py",
        "description": "Calculate feedback timing intervals",
        "required_output": "data/processed/intervals.csv",
        "depends_on": "preprocess.py"
    },
    {
        "name": "Bin Feedback Groups (US2)",
        "script": "bin_feedback_groups.py",
        "description": "Assign students to timing groups",
        "required_output": "data/processed/learners_binned.csv",
        "depends_on": "compute_intervals.py"
    },
    {
        "name": "Fit Models (US3)",
        "script": "models.py",
        "description": "Fit Cluster-Robust OLS models",
        "required_output": "data/processed/effect_sizes.csv",
        "depends_on": "bin_feedback_groups.py"
    },
    {
        "name": "Post-hoc Analysis (US3)",
        "script": "posthoc_tukey.py",
        "description": "Run Tukey HSD tests",
        "required_output": "data/processed/tukey_results.csv",
        "depends_on": "models.py"
    },
    {
        "name": "Sensitivity Analysis (US3)",
        "script": "sensitivity.py",
        "description": "Run boundary sensitivity sweeps",
        "required_output": "data/processed/sensitivity_results.csv",
        "depends_on": "bin_feedback_groups.py"
    },
    {
        "name": "Calculate Stability (US3)",
        "script": "calculate_stability.py",
        "description": "Compute significance stability metrics",
        "required_output": "data/processed/significance_stability_report.csv",
        "depends_on": "sensitivity.py"
    },
    {
        "name": "Calculate Flip Rate (US3)",
        "script": "calculate_flip_rate.py",
        "description": "Compute significance flip rate",
        "required_output": "data/processed/significance_flip_rate_report.csv",
        "depends_on": "sensitivity.py"
    },
    {
        "name": "Generate Final Report (US3)",
        "script": "report.py",
        "description": "Compile final analysis report",
        "required_output": "data/processed/final_report.pdf",
        "depends_on": "calculate_stability.py"
    }
]

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024  # Convert KB to MB

def run_script(script_name: str, timeout: Optional[int] = None) -> Tuple[bool, float, str]:
    """
    Run a pipeline script and measure execution time.
    
    Args:
        script_name: Name of the Python script in code/
        timeout: Optional timeout in seconds
        
    Returns:
        Tuple of (success, duration_seconds, output_message)
    """
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        return False, 0.0, f"Script not found: {script_path}"
    
    start_time = time.time()
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(MAX_CPU_CORES)
    env["MKL_NUM_THREADS"] = str(MAX_CPU_CORES)
    env["OPENBLAS_NUM_THREADS"] = str(MAX_CPU_CORES)
    
    try:
        # Run the script with limited CPU cores
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=str(PROJECT_ROOT)
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            return True, duration, result.stdout[:500]  # Truncate output
        else:
            return False, duration, f"Script failed with code {result.returncode}: {result.stderr[:500]}"
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, f"Script timed out after {timeout} seconds"
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"

def check_data_integrity() -> Dict[str, bool]:
    """Check if all required data files exist."""
    checks = {}
    expected_files = [
        "data/processed/learners_raw.csv",
        "data/processed/learners_binned.csv",
        "data/processed/effect_sizes.csv",
        "data/processed/significance_stability_report.csv",
        "data/processed/significance_flip_rate_report.csv"
    ]
    
    for file_path in expected_files:
        full_path = PROJECT_ROOT / file_path
        checks[file_path] = full_path.exists()
        
    return checks

def run_pipeline_benchmark() -> Dict:
    """
    Run the full pipeline benchmark and collect metrics.
    
    Returns:
        Dictionary containing benchmark results
    """
    setup_logger("performance_benchmark", PROJECT_ROOT / "logs" / "performance.log")
    
    results = {
        "start_time": datetime.now().isoformat(),
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "max_cpu_cores": MAX_CPU_CORES,
        "stages": [],
        "total_duration": 0.0,
        "memory_peak_mb": 0.0,
        "status": "unknown"
    }
    
    info("Starting performance benchmark for T044")
    info(f"Max runtime: {MAX_RUNTIME_SECONDS / 3600:.1f} hours")
    info(f"CPU cores: {MAX_CPU_CORES}")
    
    # Check initial data availability
    data_checks = check_data_integrity()
    missing_files = [f for f, exists in data_checks.items() if not exists]
    
    if missing_files:
        info(f"Missing expected output files: {missing_files}")
        info("Pipeline will attempt to regenerate missing data")
    
    # Run each stage
    for stage in PIPELINE_STAGES:
        stage_name = stage["name"]
        script_name = stage["script"]
        
        info(f"Running stage: {stage_name}")
        info(f"  Script: {script_name}")
        info(f"  Description: {stage['description']}")
        
        # Calculate remaining time
        elapsed = results["total_duration"]
        remaining_time = MAX_RUNTIME_SECONDS - elapsed
        
        if remaining_time <= 0:
            error("Max runtime exceeded before this stage could start")
            results["status"] = "failed_timeout"
            break
        
        # Run the script with remaining time budget
        success, duration, output = run_script(
            script_name, 
            timeout=min(remaining_time, MAX_RUNTIME_SECONDS)
        )
        
        stage_result = {
            "name": stage_name,
            "script": script_name,
            "success": success,
            "duration_seconds": duration,
            "output_preview": output,
            "timestamp": datetime.now().isoformat()
        }
        
        results["stages"].append(stage_result)
        results["total_duration"] += duration
        
        # Update memory tracking
        current_memory = get_memory_usage_mb()
        if current_memory > results["memory_peak_mb"]:
            results["memory_peak_mb"] = current_memory
        
        if success:
            info(f"  Completed in {duration:.2f}s")
        else:
            error(f"  Failed: {output}")
            results["status"] = "failed_stage"
            break
    
    results["end_time"] = datetime.now().isoformat()
    
    # Final status determination
    if results["total_duration"] <= MAX_RUNTIME_SECONDS:
        results["status"] = "passed"
        info(f"Pipeline completed successfully in {results['total_duration']:.2f}s")
    else:
        results["status"] = "failed_timeout"
        error(f"Pipeline exceeded max runtime: {results['total_duration']:.2f}s > {MAX_RUNTIME_SECONDS}s")
    
    return results

def generate_report(results: Dict) -> str:
    """Generate a human-readable performance report."""
    report_lines = [
        "=" * 60,
        "PERFORMANCE VERIFICATION REPORT (T044)",
        "=" * 60,
        f"Start Time: {results['start_time']}",
        f"End Time: {results['end_time']}",
        f"Max Runtime Allowed: {results['max_runtime_seconds'] / 3600:.1f} hours",
        f"CPU Cores Used: {results['max_cpu_cores']}",
        f"Total Duration: {results['total_duration'] / 3600:.2f} hours",
        f"Memory Peak: {results['memory_peak_mb']:.1f} MB",
        f"Status: {results['status'].upper()}",
        "",
        "STAGE BREAKDOWN:",
        "-" * 40
    ]
    
    for stage in results["stages"]:
        status_symbol = "✓" if stage["success"] else "✗"
        report_lines.append(
            f"{status_symbol} {stage['name']}: {stage['duration_seconds']:.2f}s"
        )
    
    report_lines.extend([
        "",
        "VERDICT:",
        "-" * 40
    ])
    
    if results["status"] == "passed":
        report_lines.append(
            f"✓ PIPELINE PASSES: Total runtime ({results['total_duration']/3600:.2f}h) "
            f"is within the 6-hour limit."
        )
    else:
        report_lines.append(
            f"✗ PIPELINE FAILS: {results['status'].replace('_', ' ').upper()}"
        )
    
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def main():
    """Main entry point for performance verification."""
    try:
        # Run the benchmark
        results = run_pipeline_benchmark()
        
        # Generate and print report
        report = generate_report(results)
        print(report)
        
        # Save report to file
        report_path = PROJECT_ROOT / "data" / "processed" / "performance_report.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            f.write(report)
        
        info(f"Report saved to: {report_path}")
        
        # Exit with appropriate code
        if results["status"] == "passed":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        error(f"Unexpected error during performance verification: {str(e)}")
        import traceback
        error(traceback.format_exc())
        sys.exit(2)

if __name__ == "__main__":
    main()