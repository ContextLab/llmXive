"""
Memory Profiling Module.
Profiles memory usage of key pipeline scripts (ingest.py, modeling.py)
using memory_profiler and psutil.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging import get_logger
from config import get_path

logger = get_logger(__name__)

def run_with_memory_profile(script_path: Path, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run a Python script under memory_profiler and capture the output.
    
    Args:
        script_path: Path to the script to profile
        args: Optional list of command line arguments to pass to the script
        
    Returns:
        Dictionary containing execution stats and memory metrics
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
        
    cmd = [
        sys.executable, "-m", "memory_profiler", 
        "--include-children", "--multiprocess"
    ]
    
    if args:
        cmd.extend(args)
        
    cmd.append(str(script_path))
    
    logger.info(f"Running memory profile for: {' '.join(cmd)}")
    
    result = {
        "script": script_path.name,
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running",
        "output_lines": [],
        "peak_memory_mb": 0.0,
        "total_memory_increase_mb": 0.0,
        "error": None
    }
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=os.environ
        )
        
        result["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        result["status"] = "success" if proc.returncode == 0 else "failed"
        
        # Combine stdout and stderr for analysis
        output = proc.stdout + proc.stderr
        result["output_lines"] = output.split('\n')
        
        # Parse memory_profiler output for peak memory
        peak_memory = 0.0
        for line in result["output_lines"]:
            if "Maximum memory usage" in line or "Mem" in line:
                try:
                    # Extract numeric values from lines like "Mem: 123.45 MiB"
                    parts = line.split()
                    for part in parts:
                        try:
                            val = float(part)
                            if val > peak_memory:
                                peak_memory = val
                        except ValueError:
                            continue
                except Exception:
                    continue
                    
        result["peak_memory_mb"] = peak_memory
        
        if proc.returncode != 0:
            result["error"] = proc.stderr.strip()
            logger.error(f"Script failed with return code {proc.returncode}: {result['error']}")
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Execution timed out after 300 seconds"
        logger.error(result["error"])
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Profiling error: {e}")
        
    return result

def profile_pipeline_scripts() -> Dict[str, Any]:
    """
    Profile memory usage of ingest.py and modeling.py.
    
    Returns:
        Dictionary with profiling results for each script
    """
    project_root = get_path("PROJECT_ROOT")
    results = {
        "profile_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scripts": {}
    }
    
    scripts_to_profile = [
        "code/ingest.py",
        "code/modeling.py"
    ]
    
    for script_rel_path in scripts_to_profile:
        script_path = Path(project_root) / script_rel_path
        
        if not script_path.exists():
            logger.warning(f"Script not found: {script_path}")
            results["scripts"][script_rel_path] = {
                "status": "not_found",
                "error": f"Script not found: {script_path}"
            }
            continue
            
        logger.info(f"Profiling {script_rel_path}...")
        script_result = run_with_memory_profile(script_path)
        results["scripts"][script_rel_path] = script_result
        
        # Save individual report
        output_dir = Path(project_root) / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        individual_report_path = output_dir / f"memory_profile_{Path(script_rel_path).stem}.json"
        with open(individual_report_path, 'w') as f:
            json.dump(script_result, f, indent=2)
            logger.info(f"Saved individual report: {individual_report_path}")
            
    # Save combined report
    combined_report_path = output_dir / "memory_profile_combined.json"
    with open(combined_report_path, 'w') as f:
        json.dump(results, f, indent=2)
        logger.info(f"Saved combined report: {combined_report_path}")
        
    return results

def generate_summary_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary report from profiling results.
    
    Args:
        results: Profiling results dictionary
        
    Returns:
        Summary report string
    """
    lines = [
        "# Memory Profiling Report",
        f"Generated: {results.get('profile_timestamp', 'N/A')}",
        "",
        "## Summary"
    ]
    
    for script_path, script_result in results.get("scripts", {}).items():
        lines.append(f"\n### {script_path}")
        lines.append(f"- Status: {script_result.get('status', 'unknown')}")
        lines.append(f"- Peak Memory: {script_result.get('peak_memory_mb', 0.0):.2f} MB")
        
        if script_result.get("error"):
            lines.append(f"- Error: {script_result['error']}")
            
    # Add recommendations based on memory usage
    lines.append("\n## Recommendations")
    max_mem = 0
    for script_result in results.get("scripts", {}).values():
        mem = script_result.get("peak_memory_mb", 0.0)
        if mem > max_mem:
            max_mem = mem
            
    if max_mem > 6000:  # 6GB threshold
        lines.append("- ⚠️ Peak memory usage exceeds 6GB. Consider reducing MAX_BLOCKS or using streaming.")
    elif max_mem > 4000:
        lines.append("- ⚠️ Peak memory usage is high (>4GB). Monitor closely during full runs.")
    else:
        lines.append("- ✅ Memory usage is within acceptable limits.")
        
    return "\n".join(lines)

def main():
    """Main entry point for memory profiling."""
    logger.info("Starting memory profiling pipeline")
    
    try:
        results = profile_pipeline_scripts()
        summary = generate_summary_report(results)
        
        # Save summary report
        project_root = get_path("PROJECT_ROOT")
        report_path = Path(project_root) / "data" / "results" / "memory_profile_summary.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(summary)
            
        logger.info(f"Memory profiling complete. Report saved to {report_path}")
        print(summary)
        
    except Exception as e:
        logger.error(f"Memory profiling failed: {e}")
        raise

if __name__ == "__main__":
    main()
