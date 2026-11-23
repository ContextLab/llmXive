"""
Wrapper script to run the pipeline with memory_profiler for T044.
Usage: python code/profile_pipeline.py
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    main_script = project_root / "code" / "main.py"
    
    if not main_script.exists():
        print(f"Error: {main_script} not found.")
        sys.exit(1)

    # Ensure memory_profiler is available (it should be in requirements.txt per T002)
    try:
        import memory_profiler
    except ImportError:
        print("Error: memory_profiler not installed. Please run: pip install memory-profiler")
        sys.exit(1)

    # Command to run with memory profiler
    cmd = [
        sys.executable, "-m", "memory_profiler",
        str(main_script),
        "--train"
    ]

    print(f"Running: {' '.join(cmd)}")
    print("This will profile the pipeline execution. Check output for memory usage per line.")
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
