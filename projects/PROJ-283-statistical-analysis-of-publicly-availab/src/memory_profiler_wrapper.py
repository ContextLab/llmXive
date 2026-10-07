"""
Memory profiling wrapper for the chess Elo analysis pipeline.

This script runs the main pipeline with memory profiling enabled and
saves the results to data/results/memory_profile.txt.

Requirements:
- memory-profiler package must be installed (added to requirements.txt)
- The pipeline must run successfully to produce valid measurements
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure output directory exists
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RESULTS_DIR / "memory_profile.txt"

def run_profiler():
    """Run the main pipeline with memory profiler and capture output."""
    
    main_script = PROJECT_ROOT / "src" / "main.py"
    
    if not main_script.exists():
        print(f"ERROR: Main script not found at {main_script}")
        sys.exit(1)
    
    # Build the memory profiler command
    cmd = [
        sys.executable,
        "-m",
        "memory_profiler",
        "--line-by-line",
        "--output-format=text",
        f"--output-file={OUTPUT_FILE}",
        str(main_script),
        "--sample"
    ]
    
    print(f"Running memory profiler with command: {' '.join(cmd)}")
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False
        )
        
        # Write stdout/stderr to the output file as well for completeness
        with open(OUTPUT_FILE, "a") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("STDOUT:\n")
            f.write(result.stdout + "\n")
            f.write("=" * 80 + "\n")
            f.write("STDERR:\n")
            f.write(result.stderr + "\n")
            f.write("=" * 80 + "\n")
            f.write(f"Return code: {result.returncode}\n")
        
        if result.returncode == 0:
            print(f"SUCCESS: Memory profile saved to {OUTPUT_FILE}")
            print(f"Pipeline completed successfully")
        else:
            print(f"WARNING: Pipeline exited with code {result.returncode}")
            print(f"Check {OUTPUT_FILE} for details")
            
        return result.returncode
        
    except FileNotFoundError as e:
        print(f"ERROR: memory_profiler not found. Install with: pip install memory-profiler")
        print(f"Original error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run memory profiler: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Profile RAM usage of the chess Elo analysis pipeline"
    )
    parser.parse_args()
    
    exit_code = run_profiler()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
