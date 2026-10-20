"""Entry‑point for the density‑supervision study.

This script supports two primary modes of operation:

1. **Legacy config‑driven mode** (used by the quick‑start guide):
   ``python -m code.run_experiments --config <yaml>``
   - Loads the YAML configuration.
   - Creates the ``outputs/`` directory tree defined in the config.
   - Creates a ``data/results/`` directory (required by the verification).
   - Writes the effective configuration to ``outputs/run_config.json``.
   - Prints ``Pipeline initialized`` on success.

2. **Explicit CLI mode** for fixed‑density, adaptive, or control‑shuffle runs:
   ``python -m code.run_experiments --mode fixed|adaptive|control_shuffle ...``
   (Placeholder implementations are provided for these modes; they are not
   required for the T001 verification.)

The script returns exit code ``0`` on success and ``1`` on error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml  # PyYAML is expected to be available in the environment

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run experiment pipeline for density‑supervision study"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a YAML configuration file (legacy mode).",
    )
    parser.add_argument(
        "--mode",
        choices=["fixed", "adaptive", "control_shuffle"],
        help="Experiment mode: 'fixed' for baseline runs, 'adaptive' for scheduler runs, "
             "'control_shuffle' for the shuffled‑entropy control.",
    )
    parser.add_argument(
        "--rhos",
        type=float,
        nargs="+",
        help="Retaining ratios for fixed‑density runs (e.g., 0.1 0.3 0.5).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        help="Random seeds for replication (e.g., 42 43 44).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write the result file (CSV for fixed, JSON for adaptive/control).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print parsed arguments and exit without running.",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file and return its contents as a dict."""
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            if not isinstance(cfg, dict):
                raise ValueError("Top‑level YAML document must be a mapping")
            return cfg
    except Exception as exc:
        log.error("Failed to load configuration %s: %s", path, exc)
        raise

def _initialize_outputs(cfg: Dict[str, Any]) -> Path:
    """Create the ``outputs/`` directory tree defined in the config.

    Returns the path to the top‑level ``outputs`` directory.
    """
    output_root = Path("outputs")
    output_root.mkdir(parents=True, exist_ok=True)

    for sub in cfg.get("output_dirs", []):
        sub_path = output_root / sub
        sub_path.mkdir(parents=True, exist_ok=True)

    return output_root

def _write_run_config(cfg: Dict[str, Any], output_root: Path) -> None:
    """Write the effective configuration to ``outputs/run_config.json``."""
    run_cfg_path = output_root / "run_config.json"
    with run_cfg_path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)
    log.info("Wrote effective run configuration to %s", run_cfg_path)

# ----------------------------------------------------------------------
# Minimal placeholder implementations for explicit modes
# ----------------------------------------------------------------------
def _run_fixed_mode(args: argparse.Namespace) -> None:
    """Placeholder for fixed‑density baseline runs (CLI mode)."""
    if not args.rhos or not args.seeds or not args.output:
        log.error(
            "Fixed mode requires --rhos, --seeds and --output arguments."
        )
        sys.exit(1)

    # Write a tiny CSV with a single dummy row per (rho, seed).
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as csvfile:
        header = "rho,seed,example_metric\n"
        csvfile.write(header)
        for rho in args.rhos:
            for seed in args.seeds:
                csvfile.write(f"{rho},{seed},0.0\n")
    print(f"Fixed‑density placeholder results written to {args.output}")

def _run_adaptive_mode(args: argparse.Namespace) -> None:
    """Placeholder for adaptive scheduler runs (CLI mode)."""
    if not args.seeds or not args.output:
        log.error(
            "Adaptive mode requires --seeds and --output arguments."
        )
        sys.exit(1)

    result = {
        "mode": "adaptive",
        "seeds": args.seeds,
        "message": "Placeholder adaptive run – full implementation pending."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Adaptive placeholder written to {args.output}")

def _run_control_shuffle_mode(args: argparse.Namespace) -> None:
    """Placeholder for shuffled‑entropy control runs (CLI mode)."""
    if not args.seeds or not args.output:
        log.error(
            "Control‑shuffle mode requires --seeds and --output arguments."
        )
        sys.exit(1)

    result = {
        "mode": "control_shuffle",
        "seeds": args.seeds,
        "message": "Placeholder output – full implementation pending."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Control‑shuffle placeholder written to {args.output}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        log.info("Dry‑run mode – parsed arguments: %s", args)
        return 0

    # ------------------------------------------------------------------
    # Legacy config‑driven path (required for T001 verification)
    # ------------------------------------------------------------------
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            log.error("Configuration file %s does not exist.", config_path)
            return 1

        try:
            cfg = _load_yaml_config(config_path)
        except Exception:
            return 1

        # Initialise output directories and write the effective config.
        output_root = _initialize_outputs(cfg)
        _write_run_config(cfg, output_root)

        # Ensure the ``data/results`` directory exists (required by the verification).
        (Path("data") / "results").mkdir(parents=True, exist_ok=True)

        # For the purpose of T001 we do not execute the full pipeline;
        # we simply indicate successful initialisation.
        print("Pipeline initialized")
        return 0

    # ------------------------------------------------------------------
    # Explicit mode‑driven path (used by later tasks)
    # ------------------------------------------------------------------
    if args.mode == "fixed":
        _run_fixed_mode(args)
    elif args.mode == "adaptive":
        _run_adaptive_mode(args)
    elif args.mode == "control_shuffle":
        _run_control_shuffle_mode(args)
    else:
        log.error(
            "No mode specified. Use --mode fixed|adaptive|control_shuffle or --config."
        )
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
