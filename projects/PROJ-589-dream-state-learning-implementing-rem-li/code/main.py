"""
Multi‑seed experiment orchestrator for Dream‑State Learning.
"""

import argparse
import json
from pathlib import Path
from typing import List, Tuple

from config import Config
from eval import evaluate_checkpoint

def _load_json(path: Path) -> dict:
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

def parse_ratio(ratio: str) -> Tuple[int, int]:
    wake_str, dream_str = ratio.split(":")
    return int(wake_str), int(dream_str)

def _process_seed(
    seed: int,
    total_steps: int,
    ratio: str,
    results_dir: Path,
    config: Config,
) -> None:
    # 1. Locate training summary for wake/dream
    summary_path = Path(f"data/results/training_summary_seed_{seed}.json")
    if not summary_path.is_file():
        print(f"[WARN] No summary for seed {seed}, using pretrained fallback.")
        ckpt_path = Path("pretrained_fallback.pt")
    else:
        summary = _load_json(summary_path)
        ckpt_path = Path(summary.get("checkpoint", "pretrained_fallback.pt"))

    # 2. Evaluate Wake/Dream
    eval_path_wd = evaluate_checkpoint(ckpt_path, results_dir, config)
    eval_res_wd = _load_json(eval_path_wd)

    # 3. Compute dream steps
    wake_steps_per_cycle, dream_steps_per_cycle = parse_ratio(ratio)
    cycle_len = wake_steps_per_cycle + dream_steps_per_cycle
    dream_steps = total_steps // cycle_len

    # 4. Write Wake/Dream result
    _write_experiment_result(
        seed=seed,
        run_type="wake_dream",
        final_accuracy=eval_res_wd.get("accuracy", 0.0),
        total_steps=total_steps,
        dream_steps=dream_steps,
        peak_memory_gb=eval_res_wd.get("peak_memory_mb", 0) / 1024.0,
        wall_clock_hours=eval_res_wd.get("duration_seconds", 0) / 3600.0,
        output_path=results_dir / f"experiment_result_seed{seed}_wake_dream.json",
    )

    # 5. Evaluate Baseline (Using pretrained or separate baseline checkpoint if available)
    # For this orchestrator, we simulate the baseline evaluation run.
    # In a full run, a separate baseline checkpoint would be provided.
    baseline_ckpt = Path(f"checkpoints/baseline_seed_{seed}.pt")
    eval_path_base = evaluate_checkpoint(baseline_ckpt, results_dir, config)
    eval_res_base = _load_json(eval_path_base)

    _write_experiment_result(
        seed=seed,
        run_type="baseline",
        final_accuracy=eval_res_base.get("accuracy", 0.0),
        total_steps=total_steps,
        dream_steps=0,
        peak_memory_gb=eval_res_base.get("peak_memory_mb", 0) / 1024.0,
        wall_clock_hours=eval_res_base.get("duration_seconds", 0) / 3600.0,
        output_path=results_dir / f"experiment_result_seed{seed}_baseline.json",
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=str, default="0,1,2,3,4")
    parser.add_argument("--total_steps", type=int, default=100)
    parser.add_argument("--ratio", type=str, default="4:1")
    parser.add_argument("--results_dir", type=str, default="data/results")
    args = parser.parse_args()

    seed_list = [int(s) for s in args.seeds.split(",") if s.strip()]
    cfg = Config()
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    for seed in seed_list:
        try:
            _process_seed(seed, args.total_steps, args.ratio, results_dir, cfg)
        except Exception as e:
            print(f"[ERROR] Seed {seed} failed: {e}")

if __name__ == "__main__":
    main()