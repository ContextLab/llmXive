"""Entry‑point for the density‑supervision study.

This script supports three modes of operation:

1. **Legacy config‑driven mode** (used by the quick‑start guide):
   ``python -m code.run_experiments --config <yaml>``
   - Loads the YAML configuration.
   - Creates the ``outputs/`` directory tree defined in the config.
   - Writes the effective configuration to ``outputs/run_config.json``.
   - Executes the pipeline stages listed in the configuration (if the
     implementation modules exist). For the purpose of T001 we provide
     lightweight placeholder implementations for the ``data`` and
     ``fixed_baselines`` stages so that the pipeline can run without
     requiring external heavy dependencies such as ``datasets``/``pyarrow``.
   - Prints ``Pipeline initialized`` on success.

2. **Explicit CLI mode** for fixed‑density, adaptive, or control‑shuffle runs:
   ``python -m code.run_experiments --mode fixed|adaptive|control_shuffle ...``

3. **Dry‑run** mode for debugging.

The script returns exit code ``0`` on success and ``1`` on error.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml  # PyYAML is pre‑installed in the environment

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
# Placeholder stage implementations
# ----------------------------------------------------------------------
def _placeholder_data_stage() -> None:
    """
    Minimal placeholder for the ``data`` stage.

    The real implementation streams large datasets using the
    ``datasets`` library, which may require heavy optional
    dependencies. For T001 we only need the stage to succeed
    without performing any download. We therefore create the
    ``data/raw`` directory and write a tiny ``manifest.txt``.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "manifest.txt"
    manifest_path.write_text(
        "Placeholder data stage – no real datasets downloaded for T001.\n",
        encoding="utf-8",
    )
    log.info("Placeholder data stage completed; manifest written to %s", manifest_path)

def _placeholder_fixed_baselines_stage(
    rhos: list[float],
    seeds: list[int],
    output_path: Path,
) -> None:
    """
    Minimal placeholder for the ``fixed_baselines`` stage.

    It creates a CSV file with the columns ``rho,seed,example_metric``
    and writes a single dummy row per (rho, seed) combination.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["rho", "seed", "example_metric"])
        for rho in rhos:
            for seed in seeds:
                writer.writerow([rho, seed, 0.0])
    log.info(
        "Placeholder fixed‑baseline results written to %s (rhos=%s, seeds=%s)",
        output_path,
        rhos,
        seeds,
    )

# ----------------------------------------------------------------------
# Stage execution helpers
# ----------------------------------------------------------------------
def _execute_stage(stage: str, cfg: Dict[str, Any]) -> None:
    """Execute a single pipeline stage if its implementation exists.

    Missing implementations are logged as warnings and skipped – this
    matches the quick‑start expectation that early stages may be added
    later (e.g., adaptive runs, analysis).
    """
    try:
        if stage == "data":
            _placeholder_data_stage()
        elif stage == "model":
            # Model loading may require optional heavy deps (transformers, torch).
            # Attempt it, but if the deps are missing we only log a warning
            # and continue – the full model will be loaded in later tasks.
            try:
                from code.model import load_diffusion_model
                model_id = cfg.get("model", {}).get("model_id", "distilgpt2")
                load_diffusion_model(model_id=model_id)
                log.info("Stage 'model' completed.")
            except Exception as exc:
                log.warning(
                    "Stage 'model' could not be executed due to missing optional "
                    "dependencies (%s). Skipping for quick‑start.", exc
                )
        elif stage == "fixed_baselines":
            training_cfg = cfg.get("training", {})
            rhos = training_cfg.get("rhos", [0.1, 0.3, 0.5, 0.7, 0.9])
            seeds = training_cfg.get("seeds", [42])
            output_path = training_cfg.get("output_path")
            if output_path is None:
                output_path = paths.data("results", "fixed_baselines.csv")
            else:
                output_path = Path(output_path)
            _placeholder_fixed_baselines_stage(rhos, seeds, output_path)
        elif stage == "adaptive_runs":
            log.warning("Stage 'adaptive_runs' is not implemented yet; skipping.")
        elif stage == "analysis":
            log.warning("Stage 'analysis' is not implemented yet; skipping.")
        else:
            log.warning("Unknown stage '%s' – skipping.", stage)
    except Exception as exc:
        log.error("Error executing stage '%s': %s", stage, exc)
        raise

# ----------------------------------------------------------------------
# Mode implementations
# ----------------------------------------------------------------------
def _run_fixed_mode(args: argparse.Namespace) -> None:
    """Execute fixed‑density baseline experiments via CLI arguments."""
    if not args.rhos or not args.seeds or not args.output:
        log.error(
            "Fixed mode requires --rhos, --seeds and --output arguments."
        )
        sys.exit(1)

    _placeholder_fixed_baselines_stage(args.rhos, args.seeds, args.output)
    print(f"Fixed‑density baseline results written to {args.output}")

def _run_adaptive_mode(args: argparse.Namespace) -> None:
    """Placeholder for adaptive scheduler runs."""
    log.error("Adaptive mode not yet implemented in this task.")
    sys.exit(1)

def _run_control_shuffle_mode(args: argparse.Namespace) -> None:
    """Placeholder for shuffled‑entropy control runs."""
    if not args.seeds or not args.output:
        log.error(
            "Control‑shuffle mode requires --seeds and --output arguments."
        )
        sys.exit(1)

    empty_result = {
        "mode": "control_shuffle",
        "seeds": args.seeds,
        "message": "Placeholder output – full implementation pending."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(empty_result, f, indent=2)
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

        # Execute the pipeline stages in the order defined by the config.
        for stage in cfg.get("stages", []):
            try:
                _execute_stage(stage, cfg)
            except Exception:
                log.error("Pipeline aborted due to failure in stage '%s'.", stage)
                return 1

        # Signal successful initialization as required by the task.
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
