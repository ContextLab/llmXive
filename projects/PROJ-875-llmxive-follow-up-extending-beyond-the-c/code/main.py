"""
Main entry point for the llmXive pipeline.
Configures global logging (JSON rotating file) and orchestrates the full experiment
batch for the Text Agent and Baseline runs.
"""
import argparse
import os
import sys
import subprocess
import yaml
from typing import List

# Ensure project root is in path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logger import configure_global_logging, get_logger

CONFIG_SEEDS_PATH = os.path.join(project_root, "config", "seeds.yaml")
DATA_PROCESSED_DIR = os.path.join(project_root, "data", "processed")
RESULTS_DIR = os.path.join(project_root, "results")

def parse_seed_range(seed_arg: str) -> List[int]:
    """
    Parse a seed specification string.
    Supports:
      - Comma separated list: "1,2,3"
      - Range with '..': "1..20" (inclusive)
    Returns a list of integers.
    """
    seed_arg = seed_arg.strip()
    if ".." in seed_arg:
        start_str, end_str = seed_arg.split("..")
        start, end = int(start_str), int(end_str)
        if start > end:
            raise ValueError("Start of seed range must be <= end.")
        return list(range(start, end + 1))
    else:
        return [int(s) for s in seed_arg.split(",") if s]

def write_seeds_yaml(seeds: List[int]) -> None:
    """
    Overwrite the project seeds configuration file with the supplied seed list.
    This file is read by `config_loader` and the various pipeline scripts.
    """
    os.makedirs(os.path.dirname(CONFIG_SEEDS_PATH), exist_ok=True)
    with open(CONFIG_SEEDS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(seeds, f)

def ensure_directories() -> None:
    """Create required output directories if they do not exist."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def run_subprocess(command: List[str]) -> None:
    """
    Execute a command via subprocess, raising an exception on failure.
    """
    logger = get_logger()
    logger.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(
        [sys.executable] + command,
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}")
        logger.error(f"Stdout: {result.stdout}")
        logger.error(f"Stderr: {result.stderr}")
        raise RuntimeError(f"Subprocess {' '.join(command)} failed")
    else:
        logger.info(f"Command succeeded: {' '.join(command)}")

def main() -> int:
    """
    Orchestrates the full experiment batch.

    Supported modes:
      - pilot: run a pilot batch (default 20 seeds)
      - full: run a full batch (user‑specified number of seeds)
    """
    logger = configure_global_logging()
    parser = argparse.ArgumentParser(description="llmXive experiment orchestrator")
    parser.add_argument(
        "--mode",
        choices=["pilot", "full", "scale", "render"],
        default="pilot",
        help="Execution mode",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        required=True,
        help="Seed specification (e.g., '1..20' or '1,2,3')",
    )
    args = parser.parse_args()

    try:
        seeds = parse_seed_range(args.seeds)
        logger.info(f"Parsed seeds: {seeds}")

        # Prepare environment
        ensure_directories()
        write_seeds_yaml(seeds)

        # 1. Render ASCII grids and visual frames
        logger.info("Running renderer for ASCII output")
        run_subprocess([
            "code/renderer.py",
            "--seeds",
            CONFIG_SEEDS_PATH,
            "--output",
            DATA_PROCESSED_DIR,
        ])

        logger.info("Running renderer for visual frames")
        run_subprocess([
            "code/renderer.py",
            "--seeds",
            CONFIG_SEEDS_PATH,
            "--output",
            DATA_PROCESSED_DIR,
            "--mode",
            "visual",
        ])

        # 2. Run Text‑only agent loop
        logger.info("Running Text Agent loop")
        run_subprocess(["code/agent_loop.py"])

        # 3. Run Baseline visual MLLM
        logger.info("Running Baseline runner")
        run_subprocess(["code/baseline_runner.py"])

        # 4. Score the runs (Memory Gap)
        logger.info("Running Scorer")
        run_subprocess(["code/scorer.py"])

        # 5. Perform statistical analysis
        logger.info("Running Stats aggregation")
        run_subprocess(["code/stats.py"])

        # 6. Generate checksums for data hygiene
        logger.info("Running checksum utility")
        run_subprocess([
            "utils/checksum.py",
            "--input",
            DATA_PROCESSED_DIR,
            "--output",
            os.path.join(project_root, "state", "checksums.yaml"),
        ])

        # Verify that the expected output exists
        summary_path = os.path.join(RESULTS_DIR, "statistical_summary.json")
        if not os.path.isfile(summary_path):
            logger.error(f"Expected summary file not found: {summary_path}")
            return 1

        logger.info("Experiment batch completed successfully.")
        return 0
    except Exception as e:
        logger.exception("Experiment orchestration failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
