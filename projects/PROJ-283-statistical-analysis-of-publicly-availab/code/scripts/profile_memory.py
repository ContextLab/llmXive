"""
Memory Profiling Script for llmXive Pipeline.

This script profiles the RAM usage of the main pipeline execution
using memory_profiler and saves the results to data/results/memory_profile.txt.

It wraps the execution of `python src/main.py --sample` to capture
line-by-line memory usage.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

# Ensure we can import from the code directory
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

def main():
    """Run memory profiling on the main pipeline."""
    # Define paths relative to project root
    output_file = project_root / "data" / "results" / "memory_profile.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure memory_profiler is available
    try:
        import memory_profiler
    except ImportError:
        print("ERROR: memory_profiler is not installed. Please install it via pip install memory-profiler")
        sys.exit(1)

    # Construct the command to profile
    # We use the memory_profiler module directly to profile the main.py script
    main_script = code_dir / "src" / "main.py"
    
    if not main_script.exists():
        print(f"ERROR: Main script not found at {main_script}")
        sys.exit(1)

    print(f"Starting memory profiling of {main_script} --sample ...")
    print(f"Output will be saved to: {output_file}")

    cmd = [
        sys.executable, "-m", "memory_profiler",
        "--line-by-line",
        "--output-format=text",
        f"--output-file={output_file}",
        str(main_script),
        "--sample"
    ]

    try:
        # Run the profiling command
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            check=True,
            capture_output=False,  # Allow output to stdout for immediate feedback
            text=True
        )
        
        if result.returncode == 0:
            print("\n" + "="*50)
            print("Memory profiling completed successfully.")
            print(f"Profile saved to: {output_file}")
            print("="*50)
            
            # Also print a summary if the file exists
            if output_file.exists():
                lines = output_file.read_text().splitlines()
                # Find the peak memory line if available
                peak_memory = None
                for line in lines:
                    if "peak memory" in line.lower() or "Maximum usage" in line:
                        print(f"Summary: {line.strip()}")
                        peak_memory = line.strip()
                        break
                if not peak_memory:
                    print("Profile saved. Check file for line-by-line details.")
            else:
                print("WARNING: Output file was not created despite successful exit code.")
        else:
            print(f"Profiling run failed with exit code {result.returncode}")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"Profiling command failed: {e}")
        # Even if the pipeline fails, we might have partial output, but we fail the task
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during profiling: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
