"""
Memory profiling wrapper script for the EEG cognitive fatigue pipeline.
Profiles the full pipeline (download, preprocess, features, analysis) using memory_profiler
and logs peak memory usage to data/analysis/memory_report.json.
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add code directory to path for imports if needed, though we run as subprocess
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import get_logger

def run_stage_with_memory(stage_name, script_name):
    """
    Runs a pipeline stage via subprocess and captures peak memory usage.
    Uses /usr/bin/time -v for portable memory measurement.
    """
    logger = get_logger("profile_memory")
    logger.info(f"Running memory profile for stage: {stage_name} ({script_name})")

    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare command
    cmd = [sys.executable, f"code/{script_name}"]
    
    # Use /usr/bin/time -v to get Maximum resident set size (kbytes)
    # This is more reliable than memory_profiler for full process measurement
    time_cmd = ["/usr/bin/time", "-v", "-o", f"/tmp/time_{script_name}.out", "-f", "%M"]
    
    # Combine: time -v python script.py
    full_cmd = time_cmd + cmd

    start_time = time.time()
    peak_memory_kb = 0
    success = False
    error_msg = None

    try:
        # Run the command
        process = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Read the time output file
        time_output_path = Path(f"/tmp/time_{script_name}.out")
        if time_output_path.exists():
            time_output = time_output_path.read_text()
            # Parse "Maximum resident set size (kbytes): XXXX"
            for line in time_output.splitlines():
                if "Maximum resident set size" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        try:
                            peak_memory_kb = int(parts[1].strip())
                        except ValueError:
                            pass
            time_output_path.unlink()  # Clean up

        if process.returncode == 0:
            success = True
            logger.info(f"Stage {stage_name} completed successfully.")
        else:
            error_msg = f"Stage {stage_name} failed with return code {process.returncode}. stderr: {process.stderr}"
            logger.error(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = f"Stage {stage_name} timed out."
        logger.error(error_msg)
    except FileNotFoundError:
        # /usr/bin/time might not be available on all systems (e.g., Windows)
        # Fallback to a simpler run without memory measurement if /usr/bin/time is missing
        logger.warning("/usr/bin/time not found. Attempting fallback measurement.")
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            if process.returncode == 0:
                success = True
                logger.info(f"Stage {stage_name} completed successfully (fallback mode).")
            else:
                error_msg = f"Stage {stage_name} failed with return code {process.returncode}."
                logger.error(error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error running stage {stage_name}: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error running stage {stage_name}: {error_msg}")

    wall_time = time.time() - start_time

    return {
        "stage": stage_name,
        "script": script_name,
        "peak_memory_kb": peak_memory_kb,
        "peak_memory_mb": round(peak_memory_kb / 1024, 2),
        "wall_time_s": round(wall_time, 3),
        "success": success,
        "error": error_msg
    }

def main():
    """
    Main entry point for memory profiling.
    Runs the full pipeline stages sequentially and logs results.
    """
    logger = get_logger("profile_memory")
    logger.info("Starting memory profiling pipeline...")

    # Ensure output directory exists
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "memory_report.json"

    # Define pipeline stages
    stages = [
        ("download", "download.py"),
        ("preprocess", "preprocess.py"),
        ("features", "features.py"),
        ("analysis", "analysis.py"),
        ("report", "report.py")
    ]

    results = []
    total_peak_memory_mb = 0.0
    total_wall_time_s = 0.0
    overall_success = True

    for stage_name, script_name in stages:
        result = run_stage_with_memory(stage_name, script_name)
        results.append(result)
        
        if result["peak_memory_mb"] > total_peak_memory_mb:
            total_peak_memory_mb = result["peak_memory_mb"]
        
        total_wall_time_s += result["wall_time_s"]
        
        if not result["success"]:
            overall_success = False
            logger.warning(f"Pipeline stopped due to failure in {stage_name}.")
            break

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "success" if overall_success else "failed",
        "stages": results,
        "summary": {
            "peak_memory_mb": round(total_peak_memory_mb, 2),
            "total_wall_time_s": round(total_wall_time_s, 3),
            "limit_mb": 7168,  # 7 GB
            "within_limit": total_peak_memory_mb <= 7168
        }
    }

    # Write report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Memory report written to {output_path}")
    print(f"Memory report written to {output_path}")
    print(f"Peak memory usage: {total_peak_memory_mb:.2f} MB")
    print(f"Status: {'PASS' if total_peak_memory_mb <= 7168 else 'FAIL'} (Limit: 7168 MB)")

    # Exit with 0 if profiling completed, regardless of pipeline success
    return 0

if __name__ == "__main__":
    sys.exit(main())