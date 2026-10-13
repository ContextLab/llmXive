"""
Entry point for training runs.

Implements the minimal training loop required for the quickstart commands.
It creates the requested output directory, runs a dummy step loop,
records simple CPU time and memory usage metrics, writes a JSONL file
with per‑step data, and logs a summary using the project's logging utilities.
"""
import argparse
import json
import time
from pathlib import Path

import psutil

from utils.logging import log_training_run, get_logger

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a training variant.")
    parser.add_argument("--variant", type=str, required=True, help="Training variant (student-only, baseline, grpo, etc.)")
    parser.add_argument("--env", type=str, required=True, help="Environment name (alfworld or webshop)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum number of training steps")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to write output artifacts")
    parser.add_argument(
        "--input-trajectories",
        type=str,
        default=None,
        help="Path to input trajectories for replay variants (optional)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Ensure output directory exists
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prepare logger
    logger = get_logger(__name__)

    logger.info("Starting training run", extra={
        "variant": args.variant,
        "environment": args.env,
        "seed": args.seed,
        "max_steps": args.max_steps,
    })

    process = psutil.Process()
    start_time = time.time()

    # Simple dummy training loop – records minimal metrics per step
    step_records = []
    for step in range(args.max_steps):
        # Dummy placeholder values – in a real implementation these would come from the agent/environment
        reward = 0.0
        done = False

        # Measure CPU time elapsed and current RSS memory (MB)
        elapsed_cpu = time.time() - start_time
        rss_mb = process.memory_info().rss / (1024 * 1024)

        record = {
            "step": step,
            "variant": args.variant,
            "environment": args.env,
            "seed": args.seed,
            "cpu_time_sec": elapsed_cpu,
            "peak_memory_mb": rss_mb,
            "reward": reward,
            "done": done,
        }
        step_records.append(record)

    # Write per‑step metrics as JSON Lines
    jsonl_path = out_dir / "run_metrics.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for rec in step_records:
            f.write(json.dumps(rec) + "\n")

    # Summarize and log the training run
    total_cpu = time.time() - start_time
    peak_memory_mb = process.memory_info().rss / (1024 * 1024)

    summary = {
        "variant": args.variant,
        "environment": args.env,
        "seed": args.seed,
        "max_steps": args.max_steps,
        "output_dir": str(out_dir),
        "total_cpu_time_sec": total_cpu,
        "peak_memory_mb": peak_memory_mb,
        "num_steps": len(step_records),
    }

    # Use the project's logging helper to persist the summary
    log_training_run(summary, log_dir=str(out_dir))

    logger.info("Training run completed", extra=summary)


if __name__ == "__main__":
    main()
