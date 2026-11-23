"""
Main entry point for the llmXive follow-up project.
Orchestrates the execution of tasks in the correct order.
"""
import argparse
import sys
import subprocess
import time
import signal
from pathlib import Path

def run_task(script_path: str, task_name: str):
    """Run a specific task script."""
    print(f"--- Running {task_name} ---")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"--- {task_name} completed successfully ---\n")
    except subprocess.CalledProcessError as e:
        print(f"--- {task_name} FAILED ---")
        raise e

def timeout_handler(signum, frame):
    print("\n⚠️  TIMEOUT: Execution exceeded the configured limit.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="llmXive Follow-up Pipeline")
    parser.add_argument("--mode", choices=["full", "data", "inference", "train", "analysis"], default="full")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout in seconds (0 for no limit)")
    args = parser.parse_args()

    # Set timeout if specified
    if args.timeout > 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)

    # Define task sequence
    tasks = []

    if args.mode in ["full", "data"]:
        tasks.append(("Data Download", "code/data/download.py"))
        tasks.append(("Data Preprocessing", "code/data/preprocess.py"))

    if args.mode in ["full", "inference"]:
        tasks.append(("Inference-Only Pass (T020)", "code/models/inference_only.py"))

    if args.mode in ["full", "train"]:
        tasks.append(("Training Loop", "code/models/anti_sd_loop.py"))

    if args.mode in ["full", "analysis"]:
        tasks.append(("Human Proxy Simulation", "code/analysis/human_proxy_sim.py"))
        tasks.append(("Statistical Analysis", "code/analysis/statistical_test.py"))
        tasks.append(("Visualization", "code/analysis/visualize.py"))

    # Execute tasks
    for name, script in tasks:
        if not Path(script).exists():
            print(f"Warning: {script} not found. Skipping {name}.")
            continue
        run_task(script, name)

    print("✅ Pipeline completed successfully.")

if __name__ == "__main__":
    main()