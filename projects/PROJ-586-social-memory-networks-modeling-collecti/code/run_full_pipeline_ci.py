"""CI pipeline runner with resource profiling.

Executes the full research pipeline on a CI runner (CPU or GPU) and records
runtime, memory usage, and disk usage for each stage.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure we can import sibling modules
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from data.loaders import load_experiment_results, save_experiment_results
from utils.logging import get_logger

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Return current process memory usage in MB (RSS)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0


def get_disk_usage_mb(path: Path) -> float:
    """Return disk usage of the given path in MB."""
    if not path.exists():
        return 0.0
    total = 0.0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024.0 * 1024.0)


def run_experiment_script(
    script_path: Path,
    args: List[str],
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Run an experiment script and capture timing, exit code, and error output."""
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=_project_root,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        exit_code = -1
        stdout = ""
        stderr = "TIMEOUT: execution exceeded allowed time"
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)

    elapsed = time.time() - start
    return {
        "exit_code": exit_code,
        "elapsed_seconds": round(elapsed, 3),
        "stdout_lines": len(stdout.splitlines()),
        "stderr_lines": len(stderr.splitlines()),
        "error_tail": stderr[-500:] if stderr else "",
    }


def run_full_pipeline(
    results_dir: Path,
    full_games: int = 1000,
    limited_games: int = 1000,
    scaling_counts: List[int] = None,
    scaling_games: int = 800,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run the full pipeline: full, limited, and scaling experiments."""
    if scaling_counts is None:
        scaling_counts = [3, 5, 7]

    pipeline_start = time.time()
    stage_results: List[Dict[str, Any]] = []

    # 1. Full-context experiment
    logger.log("run_full_context", context="full", games=full_games)
    stage_results.append(
        {
            "stage": "full_context",
            "script": "run_experiment.py",
            "args": ["--context", "full", "--agents", "5", "--games", str(full_games), "--seed", str(seed)],
            **run_experiment_script(
                _project_root / "code" / "run_experiment.py",
                ["--context", "full", "--agents", "5", "--games", str(full_games), "--seed", str(seed)],
            ),
        }
    )

    # 2. Limited-context experiment
    logger.log("run_limited_context", context="limited", games=limited_games)
    stage_results.append(
        {
            "stage": "limited_context",
            "script": "run_experiment.py",
            "args": ["--context", "limited", "--agents", "5", "--games", str(limited_games), "--seed", str(seed)],
            **run_experiment_script(
                _project_root / "code" / "run_experiment.py",
                ["--context", "limited", "--agents", "5", "--games", str(limited_games), "--seed", str(seed)],
            ),
        }
    )

    # 3. Scaling experiment
    for count in scaling_counts:
        logger.log("run_scaling", agents=count, games=scaling_games)
        stage_results.append(
            {
                "stage": f"scaling_agents_{count}",
                "script": "run_scaling_experiment.py",
                "args": ["--agents", str(count), "--games", str(scaling_games)],
                **run_experiment_script(
                    _project_root / "code" / "run_scaling_experiment.py",
                    ["--agents", str(count), "--games", str(scaling_games)],
                ),
            }
        )

    pipeline_elapsed = time.time() - pipeline_start

    # Resource snapshots
    final_memory_mb = get_memory_usage_mb()
    final_disk_mb = get_disk_usage_mb(results_dir)

    return {
        "pipeline_elapsed_seconds": round(pipeline_elapsed, 3),
        "final_memory_mb": round(final_memory_mb, 2),
        "final_disk_mb": round(final_disk_mb, 2),
        "stages": stage_results,
        "timestamp": datetime.utcnow().isoformat(),
    }


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save pipeline results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("save_pipeline_results", path=str(output_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run full pipeline with resource profiling on CI")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=_project_root / "results",
        help="Directory to store pipeline results",
    )
    parser.add_argument("--full-games", type=int, default=1000, help="Games for full-context experiment")
    parser.add_argument("--limited-games", type=int, default=1000, help="Games for limited-context experiment")
    parser.add_argument(
        "--scaling-counts",
        type=int,
        nargs="+",
        default=[3, 5, 7],
        help="Agent counts for scaling experiment",
    )
    parser.add_argument("--scaling-games", type=int, default=800, help="Games per scaling configuration")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON file path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    results_dir = args.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    logger.log("start_pipeline", results_dir=str(results_dir))

    results = run_full_pipeline(
        results_dir=results_dir,
        full_games=args.full_games,
        limited_games=args.limited_games,
        scaling_counts=args.scaling_counts,
        scaling_games=args.scaling_games,
        seed=args.seed,
    )

    output_path = args.output or results_dir / "pipeline_ci_results.json"
    save_results(results, output_path)

    logger.log("pipeline_complete", output=str(output_path))
    print(f"Pipeline results written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
