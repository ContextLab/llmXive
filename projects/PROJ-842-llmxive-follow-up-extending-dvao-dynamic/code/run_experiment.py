import argparse
import subprocess
import sys
import os

def run_command(cmd):
    """
    Runs a shell command and raises an error if it fails.
    """
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    print(f"Command succeeded: {cmd}")

def main():
    parser = argparse.ArgumentParser(description="Run the full experiment suite.")
    parser.add_argument("--full-sweep", action="store_true", help="Run the full experiment sweep.")
    parser.add_argument("--N", type=int, help="Number of objectives for a specific run.")
    parser.add_argument("--k", type=float, help="Window size ratio for a specific run.")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs for a specific run.")
    
    args = parser.parse_args()
    
    if args.full_sweep:
        # Run the full sweep
        run_command("python code/src/main.py --full-sweep")
    elif args.N and args.k:
        # Run a specific configuration
        for i in range(args.runs):
            run_command(f"python code/src/main.py --N {args.N} --k {args.k} --run-id {i}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
