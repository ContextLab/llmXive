"""
Pipeline profiler for CI verification.
Runs the full experiment pipeline and records runtime, memory, and disk usage.
"""
import argparse
import os
import sys
import time
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logging import get_logger, log_experiment_start, log_experiment_end
from utils.config import get_config

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        # Get memory usage of current process
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux
        return usage.ru_maxrss / 1024.0
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0.0

def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.exists():
                total_size += filepath.stat().st_size
    return total_size / (1024 * 1024)

def run_experiment_script(script_name: str, args: Optional[list] = None) -> bool:
    """Run an experiment script and return success status."""
    script_path = code_dir / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(code_dir),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per script
        )
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"Script failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info(f"Script completed in {elapsed:.2f}s")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False

def run_full_pipeline() -> Dict[str, Any]:
    """Run the full pipeline and collect metrics."""
    results = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scripts": [],
        "total_runtime_seconds": 0,
        "peak_memory_mb": 0.0,
        "disk_usage_mb": 0.0,
        "constraints": {
            "max_runtime_hours": 6,
            "max_memory_gb": 7,
            "max_disk_gb": 14
        },
        "passed": True
    }

    initial_memory = get_memory_usage_mb()
    initial_disk = get_disk_usage_mb(code_dir.parent / "results")
    start_time = time.time()

    # Define scripts to run in order
    scripts_to_run = [
        # US-1: Full context experiment (1000 games)
        ("run_experiment.py", ["--context", "full", "--agents", "3", "--games", "1000"]),
        # US-2: Limited context experiment (1000 games)
        ("run_limited_context_experiment.py", ["--games", "1000"]),
        # US-3: Scaling experiment (800 games each for 3, 5, 7 agents)
        ("run_experiment.py", ["--context", "scaling", "--games", "800"]),
        # Analysis: ANOVA
        ("code/analysis/anova.py", []),
        # Analysis: Power analysis
        ("code/analysis/power.py", []),
        # Analysis: Scaling analysis
        ("code/analysis/scaling.py", []),
        # Analysis: Sensitivity analysis
        ("code/analysis/sensitivity.py", []),
    ]

    for script_name, script_args in scripts_to_run:
        logger.info(f"Running {script_name}...")
        script_start = time.time()
        success = run_experiment_script(script_name, script_args)
        script_elapsed = time.time() - script_start

        script_result = {
            "script": script_name,
            "args": script_args,
            "success": success,
            "elapsed_seconds": script_elapsed,
            "memory_at_completion_mb": get_memory_usage_mb()
        }
        results["scripts"].append(script_result)
        results["peak_memory_mb"] = max(results["peak_memory_mb"], script_result["memory_at_completion_mb"])

        if not success:
            results["passed"] = False
            logger.error(f"Pipeline failed at {script_name}")
            break

    total_elapsed = time.time() - start_time
    final_memory = get_memory_usage_mb()
    final_disk = get_disk_usage_mb(code_dir.parent / "results")

    results["total_runtime_seconds"] = total_elapsed
    results["peak_memory_mb"] = max(results["peak_memory_mb"], final_memory)
    results["disk_usage_mb"] = final_disk

    # Check constraints
    runtime_hours = total_elapsed / 3600
    memory_gb = results["peak_memory_mb"] / 1024
    disk_gb = results["disk_usage_mb"] / 1024

    logger.info(f"Total runtime: {runtime_hours:.2f} hours")
    logger.info(f"Peak memory: {memory_gb:.2f} GB")
    logger.info(f"Disk usage: {disk_gb:.2f} GB")

    if runtime_hours > results["constraints"]["max_runtime_hours"]:
        logger.warning(f"Runtime exceeded limit: {runtime_hours:.2f}h > {results['constraints']['max_runtime_hours']}h")
        results["passed"] = False

    if memory_gb > results["constraints"]["max_memory_gb"]:
        logger.warning(f"Memory exceeded limit: {memory_gb:.2f}GB > {results['constraints']['max_memory_gb']}GB")
        results["passed"] = False

    if disk_gb > results["constraints"]["max_disk_gb"]:
        logger.warning(f"Disk exceeded limit: {disk_gb:.2f}GB > {results['constraints']['max_disk_gb']}GB")
        results["passed"] = False

    return results

def save_results(results: Dict[str, Any], output_path: Path):
    """Save results to JSON and create a human-readable report."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_path / "pipeline_profile.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {json_path}")

    # Create human-readable report
    report_path = output_path / "pipeline_profile_report.md"
    with open(report_path, 'w') as f:
        f.write("# Pipeline Profile Report\n\n")
        f.write(f"**Generated**: {results['start_time']}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Runtime**: {results['total_runtime_seconds']:.2f} seconds ({results['total_runtime_seconds']/3600:.2f} hours)\n")
        f.write(f"- **Peak Memory**: {results['peak_memory_mb']:.2f} MB ({results['peak_memory_mb']/1024:.2f} GB)\n")
        f.write(f"- **Disk Usage**: {results['disk_usage_mb']:.2f} MB ({results['disk_usage_mb']/1024:.2f} GB)\n")
        f.write(f"- **All Constraints Met**: {'✓ YES' if results['passed'] else '✗ NO'}\n\n")

        f.write("## Constraints\n\n")
        f.write(f"- Max Runtime: {results['constraints']['max_runtime_hours']} hours\n")
        f.write(f"- Max Memory: {results['constraints']['max_memory_gb']} GB\n")
        f.write(f"- Max Disk: {results['constraints']['max_disk_gb']} GB\n\n")

        f.write("## Script Execution Details\n\n")
        f.write("| Script | Args | Success | Time (s) | Memory (MB) |\n")
        f.write("|--------|------|---------|----------|-------------|\n")
        for script in results['scripts']:
            args_str = ', '.join(script['args']) if script['args'] else '-'
            status = '✓' if script['success'] else '✗'
            f.write(f"| {script['script']} | {args_str} | {status} | {script['elapsed_seconds']:.2f} | {script['memory_at_completion_mb']:.2f} |\n")

        f.write("\n## Conclusion\n\n")
        if results['passed']:
            f.write("All CI constraints were satisfied. The pipeline completed successfully within the specified limits.\n")
        else:
            f.write("One or more constraints were violated. Review the details above for specific failures.\n")

    logger.info(f"Report saved to {report_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run full pipeline and profile resources")
    parser.add_argument("--output-dir", type=str, default="results",
                      help="Output directory for results")
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    log_experiment_start("pipeline_profile", {"output_dir": str(output_path)})

    try:
        logger.info("Starting full pipeline profiling...")
        results = run_full_pipeline()
        save_results(results, output_path)

        if results['passed']:
            logger.info("Pipeline completed successfully within all constraints!")
            return 0
        else:
            logger.warning("Pipeline completed but exceeded one or more constraints.")
            return 1
    except Exception as e:
        logger.error(f"Pipeline profiling failed: {e}")
        return 1
    finally:
        log_experiment_end("pipeline_profile", {"passed": results.get('passed', False) if 'results' in locals() else False})

if __name__ == "__main__":
    sys.exit(main())
