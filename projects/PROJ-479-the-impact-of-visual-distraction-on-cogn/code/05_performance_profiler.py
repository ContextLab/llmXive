"""
Performance Profiling Module for llmXive Pipeline.

This module provides utilities to profile execution time and memory usage
for the main pipeline scripts (01_data_acquisition.py and 02_visual_metrics.py).

It logs execution times to the configured logger and writes a summary
report to results/statistics/performance_profile.md.
"""
import os
import sys
import time
import json
import logging
import resource
from typing import Dict, Any, Optional
from datetime import datetime

# Ensure we can import from the code directory
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CODE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils import get_logger, get_global_seed

# Constants
PERFORMANCE_LOG_FILE = "results/statistics/performance_profile.json"
PERFORMANCE_REPORT_FILE = "results/statistics/performance_profile.md"
TARGET_SCRIPTS = [
    ("01_data_acquisition", "code/01_data_acquisition.py"),
    ("02_visual_metrics", "code/02_visual_metrics.py"),
]

def ensure_output_dir():
    """Ensure the output directory for performance reports exists."""
    output_dir = os.path.join(ROOT_DIR, "results", "statistics")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_memory_usage_mb():
    """
    Get the current memory usage of the process in MB.
    
    Returns:
        float: Memory usage in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux
    return usage.ru_maxrss / 1024.0

def profile_script(script_name: str, script_path: str) -> Dict[str, Any]:
    """
    Profile a specific script by importing and running its main function.
    
    Args:
        script_name: Name of the script for logging/reporting.
        script_path: Relative path to the script from the project root.
        
    Returns:
        Dictionary containing profiling results.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting profiling for {script_name}...")
    
    start_time = time.time()
    start_memory = get_memory_usage_mb()
    
    result = {
        "script": script_name,
        "path": script_path,
        "status": "failed",
        "error": None,
        "duration_seconds": 0.0,
        "start_memory_mb": start_memory,
        "end_memory_mb": start_memory,
        "peak_memory_mb": start_memory
    }
    
    try:
        # Construct absolute path
        abs_path = os.path.join(ROOT_DIR, script_path)
        
        # Import the module dynamically
        module_name = os.path.splitext(os.path.basename(script_path))[0]
        
        # Add code directory to path temporarily if not already there
        code_dir = os.path.dirname(abs_path)
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
            
        # Import the module
        module = __import__(module_name)
        
        # Check if main function exists
        if hasattr(module, 'main'):
            logger.info(f"Executing main() for {script_name}...")
            # Run the main function
            # We assume main() takes no arguments based on the existing API
            module.main()
            result["status"] = "success"
        else:
            result["error"] = "No main() function found in module"
            logger.error(f"No main() function found in {script_name}")
            
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error profiling {script_name}: {e}", exc_info=True)
        result["status"] = "failed"
        
    finally:
        end_time = time.time()
        end_memory = get_memory_usage_mb()
        result["duration_seconds"] = end_time - start_time
        result["end_memory_mb"] = end_memory
        result["peak_memory_mb"] = max(start_memory, end_memory)
        
        logger.info(f"Finished profiling {script_name}: "
                   f"Duration={result['duration_seconds']:.2f}s, "
                   f"Memory={result['peak_memory_mb']:.2f}MB")
                   
    return result

def generate_markdown_report(results: list) -> str:
    """
    Generate a markdown report from profiling results.
    
    Args:
        results: List of profiling result dictionaries.
        
    Returns:
        Markdown formatted string.
    """
    report_lines = [
        "# Performance Profiling Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Random Seed: {get_global_seed()}",
        "",
        "## Summary",
        ""
    ]
    
    total_duration = sum(r["duration_seconds"] for r in results if r["status"] == "success")
    successful_runs = sum(1 for r in results if r["status"] == "success")
    
    report_lines.append(f"Total scripts profiled: {len(results)}")
    report_lines.append(f"Successful runs: {successful_runs}")
    report_lines.append(f"Failed runs: {len(results) - successful_runs}")
    report_lines.append(f"Total execution time: {total_duration:.2f} seconds")
    report_lines.append("")
    
    report_lines.append("## Detailed Results")
    report_lines.append("")
    report_lines.append("| Script | Status | Duration (s) | Start Memory (MB) | End Memory (MB) | Peak Memory (MB) |")
    report_lines.append("|--------|--------|--------------|-------------------|-----------------|------------------|")
    
    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        error_note = f" ({r['error'][:50]}...)" if r["error"] and len(r["error"]) > 50 else (f" ({r['error']})" if r["error"] else "")
        
        report_lines.append(
            f"| {r['script']} | {status_icon} {r['status']} | {r['duration_seconds']:.2f} | "
            f"{r['start_memory_mb']:.2f} | {r['end_memory_mb']:.2f} | {r['peak_memory_mb']:.2f} |{error_note}"
        )
        
    report_lines.append("")
    report_lines.append("## Notes")
    report_lines.append("- Memory usage is measured in Megabytes (MB).")
    report_lines.append("- Duration is the wall-clock time for the entire script execution.")
    report_lines.append("- If a script failed, the duration represents the time until failure.")
    
    return "\n".join(report_lines)

def main():
    """
    Main entry point for performance profiling.
    
    Profiles all target scripts and generates a report.
    """
    logger = get_logger(__name__)
    logger.info("Starting performance profiling pipeline...")
    
    ensure_output_dir()
    
    results = []
    for script_name, script_path in TARGET_SCRIPTS:
        result = profile_script(script_name, script_path)
        results.append(result)
        
        # Save individual JSON result for this run
        json_path = os.path.join(ROOT_DIR, "results", "statistics", f"perf_{script_name}.json")
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Saved individual profile to {json_path}")
    
    # Save combined results
    combined_path = os.path.join(ROOT_DIR, PERFORMANCE_LOG_FILE)
    with open(combined_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved combined results to {combined_path}")
    
    # Generate and save markdown report
    report_md = generate_markdown_report(results)
    report_path = os.path.join(ROOT_DIR, PERFORMANCE_REPORT_FILE)
    with open(report_path, 'w') as f:
        f.write(report_md)
    logger.info(f"Saved markdown report to {report_path}")
    
    logger.info("Performance profiling completed.")
    return results

if __name__ == "__main__":
    main()