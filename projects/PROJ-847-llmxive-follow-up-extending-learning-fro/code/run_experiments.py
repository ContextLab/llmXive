"""Reproducible entry point for the density-supervision study pipeline.

Usage:
    python -m code.run_experiments --config configs/quickstart.yaml

The script parses a YAML configuration file, initializes the output
directory structure, seeds all random number generators deterministically,
and dispatches the requested pipeline stages. Stages corresponding to
later tasks (data download, model loading, training, analysis) are
dispatched only when the corresponding modules exist, so this entry
point works from day one and grows with the project.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import yaml

# The toolkit is provided by the platform and already importable.
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

DEFAULT_CONFIG_PATH = Path("configs/quickstart.yaml")

# Stages implemented by later tasks; the entry point looks them up by
# name inside code/ and skips any module that does not exist yet.
STAGE_REGISTRY = {
    "data": "code.data",
    "model": "code.model",
    "fixed_baselines": "code.trainer",
    "adaptive_runs": "code.trainer",
    "analysis": "code.analysis",
}


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m code.run_experiments",
        description=(
            "Run the density-supervision study pipeline for d-OPSD "
            "diffusion LLMs from a YAML configuration file."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the YAML configuration file (default: %(default)s)",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default=None,
        choices=sorted(STAGE_REGISTRY.keys()),
        help="Run only a single pipeline stage (default: all enabled stages)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the random seed from the config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Initialize the pipeline and exit without running stages",
    )
    return parser.parse_args(argv)


def load_config(path: Path) -> dict:
    """Load and validate the YAML configuration file."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Config file not found: {path}. Provide a valid YAML config "
            "via --config (see docs/quickstart.md)."
        )
    with open(path, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping.")
    return config


def set_global_seed(seed: int) -> None:
    """Seed Python, NumPy and (if available) PyTorch RNGs deterministically."""
    random.seed(seed)
    np.random.seed(seed)
    try:  # torch is optional at this stage of the project
        import torch

        torch.manual_seed(seed)
    except ImportError:
        log.debug("PyTorch not installed yet; skipping torch.manual_seed.")


def initialize_outputs(config: dict) -> Path:
    """Create the outputs/ directory tree declared by the config."""
    outputs_root = paths.outputs()
    for sub in config.get("output_dirs", []):
        (outputs_root / sub).mkdir(parents=True, exist_ok=True)
    return outputs_root


def run_stage(stage: str, config: dict) -> None:
    """Dispatch a single pipeline stage to its implementing module."""
    module_name = STAGE_REGISTRY[stage]
    try:
        module = __import__(module_name, fromlist=["run_stage"])
    except ImportError as exc:
        log.warning(
            "Stage '%s' not implemented yet (module %s unavailable: %s); "
            "skipping. It will be added by a later task.",
            stage,
            module_name,
            exc,
        )
        return
    runner = getattr(module, "run_stage", None)
    if runner is None:
        log.warning(
            "Module %s has no run_stage() function yet; skipping stage '%s'.",
            module_name,
            stage,
        )
        return
    log.info("Running stage '%s' via %s", stage, module_name)
    runner(config)


def main(argv=None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)

    seed = args.seed if args.seed is not None else int(config.get("seed", 42))
    set_global_seed(seed)

    outputs_root = initialize_outputs(config)

    # Persist the effective run configuration for reproducibility.
    effective = dict(config)
    effective["seed"] = seed
    effective["config_path"] = str(args.config)
    with open(outputs_root / "run_config.json", "w", encoding="utf-8") as fh:
        json.dump(effective, fh, indent=2, sort_keys=True)

    print("Pipeline initialized")
    log.info(
        "Pipeline initialized (config=%s, seed=%d, outputs=%s)",
        args.config,
        seed,
        outputs_root,
    )

    if args.dry_run:
        log.info("Dry run requested; no stages executed.")
        return 0

    stages = config.get("stages", [])
    if args.stage is not None:
        stages = [args.stage]
    for stage in stages:
        if stage not in STAGE_REGISTRY:
            raise ValueError(
                f"Unknown stage '{stage}' in config. Valid stages: "
                f"{sorted(STAGE_REGISTRY)}"
            )
        run_stage(stage, config)

    print("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
