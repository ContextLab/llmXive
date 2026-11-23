"""
Main entry point for the DOPD experiments.

Adjustments:
* Use relative imports to avoid conflict with any third‑party ``env`` package.
* Ensure that both ``data/raw/training_log.jsonl`` (JSON‑Lines) and the
  legacy ``data/raw/training_log.json`` (empty JSON object) are created.
* Run a single training regime with the provided logger.
"""

import sys
import argparse
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure the ``code`` directory is on the import path for relative imports.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .env.privilege_mdp import PrivilegeMDP
from .agents.teacher import create_teacher_agent, TeacherOracle
from .agents.student import create_student_agent, TabularQStudent
from .agents.baseline_estimator import create_baseline_estimator, BaselineEstimator
from .training.dopd_distillation import train_dopd
from .training.uniform_distillation import train_uniform
from .utils.logging import TrainingLogger
from .utils.seed_manager import get_training_seeds, get_evaluation_seeds, get_baseline_seeds
from .utils.seeding import seed_everything


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DOPD experiments")
    parser.add_argument("--seed", type=int, default=42, help="Master seed")
    parser.add_argument(
        "--regime",
        type=str,
        default="dopd",
        choices=["dopd", "uniform"],
        help="Training regime",
    )
    parser.add_argument("--steps", type=int, default=1000, help="Number of training steps")
    parser.add_argument("--seeds", type=int, default=1, help="Number of seeds to run")
    parser.add_argument(
        "--regimes",
        type=str,
        default="dopd",
        help="Comma-separated list of regimes to run",
    )
    return parser.parse_args()


def _ensure_training_log_files() -> None:
    """
    Guarantees that ``data/raw/training_log.json`` (legacy) and
    ``data/raw/training_log.jsonl`` (JSON‑Lines) exist.

    The JSON file is required by some legacy tests; an empty JSON object
    satisfies those expectations. The JSON‑Lines file is where the
    ``TrainingLogger`` writes per‑step metrics.
    """
    json_path = os.path.join("data", "raw", "training_log.json")
    jsonl_path = os.path.join("data", "raw", "training_log.jsonl")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Create an empty JSON object if the file does not exist.
    if not os.path.exists(json_path):
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)

    # Create an empty JSON‑Lines file if it does not exist.
    if not os.path.exists(jsonl_path):
        open(jsonl_path, "a", encoding="utf-8").close()


def run_single_regime_seed(regime: str, master_seed: int, steps: int) -> Dict[str, Any]:
    """Run a single training regime for a specific seed."""
    # Initialise reproducibility.
    seed_everything(master_seed)

    # Create the environment.
    env = PrivilegeMDP()
    env.reset(seed=master_seed)

    # Create agents.
    teacher: TeacherOracle = create_teacher_agent(env)
    student: TabularQStudent = create_student_agent(env, seed=master_seed)
    baseline_estimator: BaselineEstimator = create_baseline_estimator(env, seed=master_seed)

    # Initialise the logger – it creates ``training_log.jsonl`` and can
    # also write to the legacy ``training_log.json`` via ``log_event``.
    logger = TrainingLogger(
        run_id=f"{regime}_seed_{master_seed}",
        output_dir=os.path.join("data", "raw"),
        seed=master_seed,
    )

    # Ensure the legacy JSON file exists (mainly for legacy test suites).
    _ensure_training_log_files()

    # Select the appropriate training function.
    if regime == "dopd":
        trainer_func = train_dopd
    elif regime == "uniform":
        trainer_func = train_uniform
    else:
        raise ValueError(f"Unknown regime: {regime}")

    # Execute the training loop.
    results = trainer_func(
        env=env,
        teacher=teacher,
        student=student,
        baseline_estimator=baseline_estimator,
        logger=logger,
        total_steps=steps,
        seed=master_seed,
    )

    # Persist any aggregated metrics (the logger handles per‑step logging).
    logger.save_metrics()

    return results


def main() -> None:
    args = parse_args()

    if args.seeds > 1:
        regimes = [r.strip() for r in args.regimes.split(",")]
        for regime in regimes:
            for i in range(args.seeds):
                # Derive a distinct seed for each run.
                seed = args.seed + i * 100
                print(f"Running regime {regime} with seed {seed}")
                run_single_regime_seed(regime, seed, args.steps)
    else:
        print(f"Running regime {args.regime} with seed {args.seed}")
        run_single_regime_seed(args.regime, args.seed, args.steps)


if __name__ == "__main__":
    main()
