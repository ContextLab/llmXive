"""
Entry‑point for the Counterfactual Consistency research pipeline.

The script reads a YAML configuration file, performs a very lightweight
“dry‑run” of the pipeline (no heavy computation), and prints a concise
summary of the configuration and the expected output artifacts.

This satisfies Task T001 by providing a reproducible one‑command entry‑point
that exits with status 0.
"""

import argparse
import sys
from pathlib import Path

import yaml

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)


def load_config(config_path: Path) -> dict:
    """Load a YAML configuration file."""
    if not config_path.is_file():
        log.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def print_summary(cfg: dict) -> None:
    """Print a short, deterministic summary of the run."""
    output_dir = Path(cfg.get("output_dir", "./output"))
    # Ensure the output directory exists (paths helper will also create subfolders)
    output_dir.mkdir(parents=True, exist_ok=True)

    # List of expected artifact directories (mirroring the quickstart table)
    artifact_dirs = {
        "Original videos": output_dir / "data" / "videos" / "orig",
        "Counterfactual videos": output_dir / "data" / "videos" / "cf",
        "Metadata CSV": output_dir / "data" / "counterfactuals" / "metadata.csv",
        "Optical‑flow features": output_dir / "data" / "flow",
        "Model checkpoints": output_dir / "checkpoints",
        "Per‑seed evaluation": output_dir / "results" / "per_seed.csv",
        "Summary CSV": output_dir / "results" / "summary.csv",
        "Figures": output_dir / "figures",
    }

    print("\n=== Counterfactual Consistency Pipeline Summary ===")
    print("Configuration:")
    for key, value in cfg.items():
        print(f"  {key}: {value}")

    print("\nExpected output locations:")
    for name, path in artifact_dirs.items():
        print(f"  {name}: {path}")

    print("\nNOTE: This run is a lightweight dry‑run that validates the entry‑point.")
    print("      Full pipeline execution is performed by the same command after"
          " implementing the remaining tasks.\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full Counterfactual Consistency pipeline (dry‑run)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a YAML configuration file (e.g., configs/run.yaml).",
    )

    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    print_summary(cfg)

    # Successful exit
    return 0


if __name__ == "__main__":
    sys.exit(main())
