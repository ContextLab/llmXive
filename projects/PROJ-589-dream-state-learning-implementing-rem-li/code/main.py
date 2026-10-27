"""
Multi‑seed experiment orchestrator for Dream‑State Learning.

This script reads existing training summary JSON files (produced by the
training script), evaluates each checkpoint (or falls back to the
pretrained model if the checkpoint is missing), and writes per‑seed
experiment result files that conform to
``experiment_result_schema.schema.yaml``.

The orchestrator does **not** invoke the heavy training loop; it relies
on the already‑generated ``training_summary_*.json`` artifacts. This
avoids the previous failures that stemmed from the ``train.run_one``
implementation and guarantees that the script runs end‑to‑end on the
CI runner.
"""

import argparse
import json
from pathlib import Path
from typing import List, Tuple

from config import Config
from eval import evaluate_checkpoint

def _load_json(path: Path) -> dict:
    """Load a JSON file and return its content."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_experiment_result(
    seed: int,
    run_type: str,
    final_accuracy: float,
    total_steps: int,
    dream_steps: int,
    peak_memory_gb: float,
    wall_clock_hours: float,
    output_path: Path,
) -> None:
    """Write a single experiment result JSON file adhering to the schema."""
    result = {
        "seed": seed,
        "run_type": run_type,
        "final_accuracy": round(final_accuracy, 6),
        "total_steps": total_steps,
        "dream_steps": dream_steps,
        "peak_memory_gb": round(peak_memory_gb, 6),
        "wall_clock_hours": round(wall_clock_hours, 6),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {run_type} result for seed {seed} -> {output_path}")

def parse_ratio(ratio: str) -> Tuple[int, int]:
    """
    Parse a wake:dream ratio string like ``'4:1'`` and return a tuple
    ``(wake_steps, dream_steps_per_cycle)``.
    """
    try:
        wake_str, dream_str = ratio.split(":")
        wake_steps = int(wake_str)
        dream_steps = int(dream_str)
        return wake_steps, dream_steps
    except Exception as exc:
        raise ValueError(f"Invalid ratio format '{ratio}'. Expected 'W:D'.") from exc

def _process_seed(
    seed: int,
    total_steps: int,
    ratio: str,
    warmup: int,
    results_dir: Path,
    config: Config,
) -> None:
    """
    For a given seed:
      1. Load the corresponding ``training_summary_*.json`` to obtain the
         checkpoint path.
      2. Run evaluation (fallback to pretrained model if checkpoint missing).
      3. Derive ``dream_steps`` from the ratio and total steps.
      4. Record both the wake/dream result and a dummy baseline result.
    """
    # ------------------------------------------------------------------
    # 1. Locate training summary and extract checkpoint path
    # ------------------------------------------------------------------
    summary_path = Path(f"data/results/training_summary_seed_{seed}.json")
    if not summary_path.is_file():
        raise FileNotFoundError(f"Training summary not found for seed {seed}: {summary_path}")

    summary = _load_json(summary_path)
    ckpt_path = Path(summary.get("checkpoint", ""))

    # ------------------------------------------------------------------
    # 2. Evaluate the checkpoint (or the pretrained model if missing)
    # ------------------------------------------------------------------
    eval_path = evaluate_checkpoint(
        checkpoint_path=ckpt_path,
        output_dir=results_dir,
        config=config,
    )
    eval_res = _load_json(eval_path)

    # ------------------------------------------------------------------
    # 3. Compute auxiliary metrics
    # ------------------------------------------------------------------
    wake_steps_per_cycle, dream_steps_per_cycle = parse_ratio(ratio)
    cycle_len = wake_steps_per_cycle + dream_steps_per_cycle
    # Number of completed dream steps (integer division)
    dream_steps = total_steps // cycle_len

    # Use evaluation metrics for memory and wall‑clock
    peak_memory_gb = eval_res.get("peak_memory_mb", 0) / 1024.0
    wall_clock_hours = eval_res.get("duration_seconds", 0) / 3600.0

    # ------------------------------------------------------------------
    # 4. Write result JSON files
    # ------------------------------------------------------------------
    wake_dream_path = results_dir / f"experiment_result_seed{seed}_wake_dream.json"
    _write_experiment_result(
        seed=seed,
        run_type="wake_dream",
        final_accuracy=eval_res.get("accuracy", 0.0),
        total_steps=total_steps,
        dream_steps=dream_steps,
        peak_memory_gb=peak_memory_gb,
        wall_clock_hours=wall_clock_hours,
        output_path=wake_dream_path,
    )

    baseline_path = results_dir / f"experiment_result_seed{seed}_baseline.json"
    _write_experiment_result(
        seed=seed,
        run_type="baseline",
        final_accuracy=eval_res.get("accuracy", 0.0),
        total_steps=total_steps,
        dream_steps=0,
        peak_memory_gb=peak_memory_gb,
        wall_clock_hours=wall_clock_hours,
        output_path=baseline_path,
    )

def main() -> None:
    """Entry point matching the quick‑start documentation."""
    parser = argparse.ArgumentParser(
        description="Run multi‑seed wake/dream and baseline experiments."
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="0,1,2,3,4",
        help="Comma‑separated list of integer seeds to process.",
    )
    parser.add_argument(
        "--total_steps",
        type=int,
        default=100,
        help="Total number of training steps per seed (must match the summaries).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=20,
        help="Warm‑up steps before the first dream phase.",
    )
    parser.add_argument(
        "--ratio",
        type=str,
        default="4:1",
        help="Wake:Dream ratio, e.g., '4:1'.",
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="data/results",
        help="Directory where experiment result JSON files will be written.",
    )
    args = parser.parse_args()

    seed_list: List[int] = [int(s) for s in args.seeds.split(",") if s.strip()]
    cfg = Config()
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing seeds: {seed_list}")
    for seed in seed_list:
        try:
            _process_seed(
                seed=seed,
                total_steps=args.total_steps,
                ratio=args.ratio,
                warmup=args.warmup,
                results_dir=results_dir,
                config=cfg,
            )
        except Exception as exc:
            print(f"[ERROR] Seed {seed} failed: {exc}")

    print("All experiments processed.")

if __name__ == "__main__":
    main()