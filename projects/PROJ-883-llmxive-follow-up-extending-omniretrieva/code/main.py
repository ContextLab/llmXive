"""Entry point for the benchmark pipeline.

This script orchestrates the full end‑to‑end flow:
  1. Ensure required output directories exist.
  2. Generate synthetic queries (writes ``generation_log.json``).
  3. Enrich the queries with a system‑generated plan via the router.
  4. Run the synthetic benchmark (writes ``execution_logs.csv``).

The script is deliberately simple – it invokes the existing CLI
wrappers for each stage using ``subprocess.run`` so that argument
parsing stays in the original modules.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)


def ensure_directories() -> None:
    """Create all required data directories."""
    for folder in [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
    log.debug("Data directories ensured.")


def _run_subprocess(command: list[str]) -> None:
    """Execute a command, raising on failure."""
    log.debug("Running command: %s", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(
            "Command failed (exit %s): %s\\nSTDOUT: %s\\nSTDERR: %s",
            result.returncode,
            " ".join(command),
            result.stdout,
            result.stderr,
        )
        sys.exit(result.returncode)
    else:
        log.debug("Command succeeded.")


def _run_generation(seed: int) -> None:
    """Generate the synthetic queries."""
    gen_cmd = [
        sys.executable,
        "-m",
        "code.query_generator",
        "--levels",
        "1",
        "2",
        "3",
        "4",
        "--count",
        "10",
        "--seed",
        str(seed),
    ]
    _run_subprocess(gen_cmd)


def _run_router() -> None:
    """Enrich the generation log with system‑generated plans."""
    gen_path = str(paths.data("processed", "generation_log.json"))
    router_cmd = [
        sys.executable,
        "-m",
        "code.router.sut_router",
        "--input",
        gen_path,
        "--output",
        gen_path,
    ]
    _run_subprocess(router_cmd)


def _run_benchmark() -> None:
    """Run the synthetic benchmark (writes execution_logs.csv)."""
    bench_cmd = [
        sys.executable,
        "-m",
        "code.benchmark_runner",
        "--throttle",
        "cgroups",
        "--timeout",
        "60",
    ]
    _run_subprocess(bench_cmd)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full benchmark pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic query generation.",
    )
    return parser


def main() -> None:
    """Main entry point."""
    args = _build_parser().parse_args()
    ensure_directories()
    _run_generation(seed=args.seed)
    _run_router()
    _run_benchmark()
    log.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
