"""
Run the full social memory networks pipeline on a CI runner and record
runtime, memory, and disk usage to verify constraints:
- Runtime <= 6 hours (21600 seconds)
- RAM <= 7 GB (7168 MB)
- Disk <= 14 GB (14336 MB)

This script executes all major experiment phases (full context, limited context,
scaling) and aggregates the resource measurements into a JSON report.
"""
import argparse
import os
import sys
import time
import subprocess
import json
import resource
from pathlib import Path
from datetime import datetime

# Ensure we can import from the code directory
CODE_ROOT = Path(__file__).parent
PROJECT_ROOT = CODE_ROOT.parent
RESULTS_DIR = PROJECT_ROOT / "results"

# Constraints
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_RAM_MB = 7 * 1024           # 7 GB
MAX_DISK_MB = 14 * 1024         # 14 GB

def get_memory_usage_mb():
    """Get current memory usage in MB (RSS)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, MB on macOS
    if sys.platform == "darwin":
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss / 1024.0

def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of the project directory in MB."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                total += filepath.stat().st_size
            except (OSError, FileNotFoundError):
                continue
    return total / (1024 * 1024)

def run_experiment_script(script_name: str, args: list = None) -> dict:
    """
    Run an experiment script and capture its runtime and peak memory.
    Returns a dict with 'script', 'runtime_seconds', 'peak_memory_mb', 'success', 'error'.
    """
    script_path = CODE_ROOT / script_name
    if not script_path.exists():
        return {
            "script": script_name,
            "success": False,
            "error": f"Script not found: {script_path}",
            "runtime_seconds": 0,
            "peak_memory_mb": 0
        }

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    start_time = time.time()
    try:
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=str(CODE_ROOT),
            capture_output=True,
            text=True,
            timeout=MAX_RUNTIME_SECONDS
        )
        success = result.returncode == 0
        error_msg = result.stderr if not success else ""
    except subprocess.TimeoutExpired:
        success = False
        error_msg = f"Script timed out after {MAX_RUNTIME_SECONDS} seconds"
    except Exception as e:
        success = False
        error_msg = str(e)

    end_time = time.time()
    runtime = end_time - start_time
    peak_mem = get_memory_usage_mb()

    return {
        "script": script_name,
        "success": success,
        "error": error_msg,
        "runtime_seconds": runtime,
        "peak_memory_mb": peak_mem
    }

def run_full_pipeline():
    """Run all pipeline stages and collect resource metrics."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "constraints": {
            "max_runtime_seconds": MAX_RUNTIME_SECONDS,
            "max_ram_mb": MAX_RAM_MB,
            "max_disk_mb": MAX_DISK_MB
        },
        "stages": [],
        "totals": {
            "total_runtime_seconds": 0,
            "peak_memory_mb": 0,
            "final_disk_mb": 0
        },
        "verdict": None,
        "details": []
    }

    # Stages to run (order matters for dependencies)
    stages = [
        ("US1: Full Context", ["run_experiment.py", "--context", "full", "--games", "100", "--agents", "3"]),
        ("US2: Limited Context", ["run_limited_context_experiment.py", "--games", "100", "--agents", "3"]),
        ("US3: Scaling", ["run_experiment.py", "--context", "full", "--games", "80", "--agents", "3,5,7"]),
        ("Analysis: ANOVA", ["code/analysis/anova.py"]),
        ("Analysis: Power", ["code/analysis/power.py"]),
        ("Analysis: Scaling", ["code/analysis/scaling.py"]),
    ]

    running_peak_mem = 0.0

    for stage_name, cmd_args in stages:
        print(f"Running stage: {stage_name}")
        script_name = cmd_args[0]
        args = cmd_args[1:] if len(cmd_args) > 1 else []

        # Get disk usage before
        disk_before = get_disk_usage_mb(PROJECT_ROOT)

        stage_result = run_experiment_script(script_name, args)
        stage_result["stage_name"] = stage_name
        stage_result["disk_before_mb"] = disk_before
        stage_result["disk_after_mb"] = get_disk_usage_mb(PROJECT_ROOT)

        if stage_result["peak_memory_mb"] > running_peak_mem:
            running_peak_mem = stage_result["peak_memory_mb"]

        report["stages"].append(stage_result)
        report["totals"]["total_runtime_seconds"] += stage_result["runtime_seconds"]
        report["totals"]["peak_memory_mb"] = max(report["totals"]["peak_memory_mb"], stage_result["peak_memory_mb"])

        print(f"  -> Success: {stage_result['success']}, Runtime: {stage_result['runtime_seconds']:.2f}s, Peak Mem: {stage_result['peak_memory_mb']:.2f}MB")

        if not stage_result["success"]:
            report["details"].append(f"Stage failed: {stage_name} - {stage_result['error']}")

    # Final disk usage
    report["totals"]["final_disk_mb"] = get_disk_usage_mb(PROJECT_ROOT)

    # Determine verdict
    all_success = all(s["success"] for s in report["stages"])
    runtime_ok = report["totals"]["total_runtime_seconds"] <= MAX_RUNTIME_SECONDS
    mem_ok = report["totals"]["peak_memory_mb"] <= MAX_RAM_MB
    disk_ok = report["totals"]["final_disk_mb"] <= MAX_DISK_MB

    if all_success and runtime_ok and mem_ok and disk_ok:
        report["verdict"] = "PASS"
        report["details"].append("All constraints satisfied.")
    else:
        report["verdict"] = "FAIL"
        if not all_success:
            report["details"].append("One or more stages failed.")
        if not runtime_ok:
            report["details"].append(f"Runtime exceeded: {report['totals']['total_runtime_seconds']:.2f}s > {MAX_RUNTIME_SECONDS}s")
        if not mem_ok:
            report["details"].append(f"Memory exceeded: {report['totals']['peak_memory_mb']:.2f}MB > {MAX_RAM_MB}MB")
        if not disk_ok:
            report["details"].append(f"Disk exceeded: {report['totals']['final_disk_mb']:.2f}MB > {MAX_DISK_MB}MB")

    return report

def save_results(report: dict, output_path: Path):
    """Save the pipeline report to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run full pipeline and profile resources")
    parser.add_argument("--output", type=str, default="pipeline_profile_report.json",
                        help="Output filename for the report")
    args = parser.parse_args()

    print("Starting full pipeline profiling...")
    print(f"Constraints: Runtime <= {MAX_RUNTIME_SECONDS}s, RAM <= {MAX_RAM_MB}MB, Disk <= {MAX_DISK_MB}MB")

    report = run_full_pipeline()
    output_path = RESULTS_DIR / args.output
    save_results(report, output_path)

    print("\n--- Summary ---")
    print(f"Verdict: {report['verdict']}")
    print(f"Total Runtime: {report['totals']['total_runtime_seconds']:.2f}s")
    print(f"Peak Memory: {report['totals']['peak_memory_mb']:.2f}MB")
    print(f"Final Disk: {report['totals']['final_disk_mb']:.2f}MB")

    if report["verdict"] == "FAIL":
        print("\nDetails:")
        for detail in report["details"]:
            print(f"  - {detail}")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
