"""
Minimal experiment runner.

Supports two modes:
* ``--debug`` – runs a single episode with user‑specified ``--alpha``,
  ``--horizon`` and ``--seed``.
* ``--grid`` – iterates over the default grid defined in
  :mod:`experiments.grid_config` and records a single‑episode metric for
  each configuration.

All results are written to ``data/raw/`` using the ``paths`` helper from
``llmxive_toolkit``.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

from env.reasoning_mdp import ReasoningMDP
from env.teacher_policy import TeacherPolicy
from student.policy import StudentPolicy
from experiments.grid_config import GridConfig, create_default_grid

logger = get_logger("experiments.runner")

def _run_episode(
    mdp: ReasoningMDP,
    teacher: TeacherPolicy,
    student: StudentPolicy,
    alpha: float,
    horizon: int,
) -> Dict[str, Any]:
    """
    Execute a single episode and return basic metrics.

    The TOP‑D loss is **not** computed here – this placeholder records the
    effective depth achieved by the student and whether it matches the
    teacher's depth.
    """
    # Teacher provides the optimal path (length = horizon)
    teacher_path = teacher.get_optimal_path(horizon)

    state = mdp.reset()
    effective_depth = 0
    for step_idx, teacher_action in enumerate(teacher_path):
        # Student selects an action based on its current Q‑table
        student_action = student.select_action(state)

        # Apply the student's action to the environment
        next_state, reward, done = mdp.step(student_action)

        # Update student Q‑table using the observed transition
        student.update(state, student_action, reward, next_state)

        state = next_state
        effective_depth = step_idx + 1

        if done:
            break

    # Simple collapse ratio: student depth / teacher depth
    collapse_ratio = effective_depth / len(teacher_path)

    return {
        "alpha": alpha,
        "horizon": horizon,
        "effective_depth": effective_depth,
        "teacher_depth": len(teacher_path),
        "collapse_ratio": collapse_ratio,
    }

def run_training_loop(config: GridConfig) -> Dict[str, Any]:
    """
    Run a single‑episode training loop for the given configuration.

    The function writes a CSV line to ``data/raw/episodes_<alpha>_<horizon>.csv``.
    """
    # Set deterministic seed for reproducibility
    np.random.seed(config.seed)

    mdp = ReasoningMDP(size=config.horizon)
    teacher = TeacherPolicy(mdp)
    student = StudentPolicy(mdp, horizon_limit=config.horizon)

    metrics = _run_episode(
        mdp=mdp,
        teacher=teacher,
        student=student,
        alpha=config.alpha,
        horizon=config.horizon,
    )

    # Persist the episode log
    output_path = paths.data("raw", f"episodes_{config.alpha}_{config.horizon}.csv")
    df = pd.DataFrame([metrics])
    df.to_csv(output_path, index=False)
    logger.info(f"Episode logged to {output_path}")

    return metrics

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TOP‑D experiments.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run a single debug episode with explicit hyper‑parameters.",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Execute the full hyper‑parameter grid.",
    )
    parser.add_argument("--alpha", type=float, default=0.5, help="Interpolation coefficient.")
    parser.add_argument("--horizon", type=int, default=5, help="Student horizon limit.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()

def main() -> int:
    args = _parse_args()

    if args.debug:
        # Build a temporary config object for the debug run
        config = GridConfig(alpha=args.alpha, horizon=args.horizon, seed=args.seed)
        run_training_loop(config)
    elif args.grid:
        configs = create_default_grid()
        for cfg in configs:
            run_training_loop(cfg)
    else:
        logger.error("Either --debug or --grid must be specified.")
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
