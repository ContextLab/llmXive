"""
Memory profiling utilities for the Urban Heat Island analysis pipeline.

This module provides tools to profile memory usage of the ingestion and modeling
scripts using the memory_profiler package. It generates detailed reports of
memory consumption at various stages of the pipeline execution.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Attempt to import memory_profiler; if missing, provide a graceful fallback
try:
    from memory_profiler import profile
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
      MEMORY_PROFILER_AVAILABLE = False
      # Define a no-op decorator if memory_profiler is not installed
      def profile(func):
          def wrapper(*args, **kwargs):
              return func(*args, **kwargs)
          return wrapper

from utils.logging import get_logger
from config import get_path

# Initialize logger
logger = get_logger(__name__)

def run_with_memory_profile(
    script_path: str,
    output_json: Optional[str] = None,
    timeout_seconds: int = 300
) -> Tuple[bool, str]:
    """
    Run a script with memory profiling enabled and capture the output.
    
    Args:
        script_path: Path to the Python script to profile (e.g., 'code/ingest.py').
        output_json: Optional path to write the memory profile summary JSON.
        timeout_seconds: Timeout for the script execution.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not MEMORY_PROFILER_AVAILABLE:
        logger.error(
            "memory_profiler is not installed. "
            "Install it via: pip install memory-profiler"
        )
        return False, "memory_profiler not installed"

    script_path_obj = Path(script_path)
    if not script_path_obj.exists():
        return False, f"Script not found: {script_path}"

    # Construct the command to run with memory profiler
    # We use the -m memory_profiler approach which outputs to stdout
    cmd = [
        sys.executable,
        "-m",
        "memory_profiler",
        "--log-file",
        str(script_path_obj.with_suffix(".memlog")),
        script_path
    ]

    # Add arguments if the script expects them (e.g., --city NYC)
    # For now, we run the main() function as defined in the script
    # The script itself should handle its own argument parsing or run with defaults

    logger.info(f"Running memory profile on {script_path}...")
    start_time = time.time()

    try:
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )

        elapsed = time.time() - start_time

        if result.returncode != 0:
            error_msg = f"Script failed with code {result.returncode}\nSTDERR: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        # Parse the memory log file if it exists
        log_file = script_path_obj.with_suffix(".memlog")
        profile_data = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Parse the memory profiler output lines
                # Format: Line #    Mem used    Increment    Line contents
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[0].isdigit():
                        try:
                            profile_data.append({
                                "line": int(parts[0]),
                                "memory_mb": float(parts[1]),
                                "increment": float(parts[2]),
                                "code": " ".join(parts[5:])
                            })
                        except ValueError:
                            continue

        # Generate summary
        summary = {
            "script": str(script_path),
            "success": True,
            "execution_time_seconds": elapsed,
            "total_lines_profiled": len(profile_data),
            "peak_memory_mb": max([p["memory_mb"] for p in profile_data]) if profile_data else 0,
            "average_memory_mb": sum([p["memory_mb"] for p in profile_data]) / len(profile_data) if profile_data else 0,
            "profile_data": profile_data
        }

        if output_json:
            with open(output_json, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Memory profile summary written to {output_json}")

        logger.info(f"Memory profiling completed in {elapsed:.2f}s. Peak memory: {summary['peak_memory_mb']:.2f} MB")
        return True, f"Success. Peak memory: {summary['peak_memory_mb']:.2f} MB"

    except subprocess.TimeoutExpired:
        return False, f"Script execution timed out after {timeout_seconds} seconds"
    except Exception as e:
        logger.exception(f"Error during memory profiling: {e}")
        return False, str(e)

def profile_pipeline_scripts(
    scripts: List[str],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Profile multiple pipeline scripts and aggregate results.
    
    Args:
        scripts: List of script paths to profile (e.g., ['code/ingest.py', 'code/modeling.py']).
        output_dir: Directory to save individual and summary reports.
        
    Returns:
        Dictionary containing aggregated profiling results.
    """
    if not MEMORY_PROFILER_AVAILABLE:
        logger.warning("memory_profiler not available. Skipping profiling.")
        return {"error": "memory_profiler not installed", "results": {}}

    output_path = Path(output_dir) if output_dir else get_path("data", "results")
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for script in scripts:
        script_name = Path(script).stem
        output_json = output_path / f"{script_name}_memory_profile.json"
        
        success, message = run_with_memory_profile(script, str(output_json))
        results[script] = {
            "success": success,
            "message": message,
            "output_file": str(output_json) if success else None
        }

    # Generate summary report
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scripts_profiled": len(scripts),
        "successful_profiles": sum(1 for r in results.values() if r["success"]),
        "results": results
    }

    summary_file = output_path / "memory_profile_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Memory profiling summary saved to {summary_file}")
    return summary

def generate_summary_report(
    profile_results: Dict[str, Any],
    threshold_mb: float = 6000.0
) -> str:
    """
    Generate a human-readable summary report from profiling results.
    
    Args:
        profile_results: Dictionary of profiling results (output of profile_pipeline_scripts).
        threshold_mb: Memory threshold in MB to flag potential issues.
        
    Returns:
        Formatted string report.
    """
    lines = [
        "# Memory Profiling Report",
        f"Generated: {profile_results.get('timestamp', 'N/A')}",
        f"Scripts Profiled: {profile_results.get('scripts_profiled', 0)}",
        f"Successful Profiles: {profile_results.get('successful_profiles', 0)}",
        "",
        "## Individual Script Results",
        ""
    ]

    for script, data in profile_results.get("results", {}).items():
        lines.append(f"### {script}")
        if data["success"]:
            lines.append(f"- Status: SUCCESS")
            if data.get("output_file"):
                lines.append(f"- Output: {data['output_file']}")
                # Try to load the specific result for peak memory
                try:
                    with open(data["output_file"], 'r') as f:
                        specific_data = json.load(f)
                        peak = specific_data.get("peak_memory_mb", 0)
                        lines.append(f"- Peak Memory: {peak:.2f} MB")
                        if peak > threshold_mb:
                            lines.append(f"- ⚠️ WARNING: Exceeds threshold of {threshold_mb} MB")
                except Exception:
                    lines.append("- Could not read detailed metrics")
        else:
            lines.append(f"- Status: FAILED")
            lines.append(f"- Error: {data['message']}")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append("- If peak memory exceeds 6GB, consider enabling spatial block sampling (T026b).")
    lines.append("- If specific functions show high memory spikes, consider chunking or streaming data.")
    lines.append("- Ensure all temporary files are cleaned up after processing.")

    return "\n".join(lines)

def main():
    """
    Main entry point for memory profiling.
    
    Profiles the ingestion and modeling scripts by default.
    """
    logger.info("Starting memory profiling pipeline...")

    # Define scripts to profile
    scripts_to_profile = [
        "code/ingest.py",
        "code/modeling.py"
    ]

    # Run profiling
    results = profile_pipeline_scripts(scripts_to_profile)

    # Generate and print report
    report = generate_summary_report(results)
    print(report)
    
    # Log the report to file as well
    log_report_path = get_path("data", "results", "memory_profile_report.md")
    with open(log_report_path, 'w') as f:
        f.write(report)
    logger.info(f"Report saved to {log_report_path}")

    return 0 if results["successful_profiles"] == len(scripts_to_profile) else 1

if __name__ == "__main__":
    sys.exit(main())