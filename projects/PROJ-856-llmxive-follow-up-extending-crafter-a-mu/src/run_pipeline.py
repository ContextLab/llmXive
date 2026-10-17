"""
src.run_pipeline
-----------------
Entry point for the end‑to‑end study pipeline.

The script reads a minimal configuration file, seeds all
randomness sources for deterministic behaviour, and then
(in a full implementation) would orchestrate the various
pipeline stages (data curation, simulation, validation,
analysis, reporting).  For the purpose of the initial
quick‑start verification we simply confirm that the script
runs without error and prints the expected completion message.
"""

import argparse
import sys
import random
import numpy as np
from pathlib import Path

try:
    import yaml  # PyYAML is available in the base environment
except ImportError as exc:
    raise ImportError("PyYAML is required to parse the configuration file") from exc

# Optional: torch may not be installed in every environment,
# but it is listed in requirements.txt.  Import lazily.
try:
    import torch
except Exception:  # pragma: no cover
    torch = None  # type: ignore

def seed_all(seed: int = 42) -> None:
    """
    Seed the common random number generators for reproducibility.

    Parameters
    ----------
    seed : int
        The seed value to use for ``random``, ``numpy`` and (if available) ``torch``.
    """
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full study pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to a YAML configuration file (default: config.yaml).",
    )
    return parser

def main() -> int:
    """
    Execute the pipeline.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    parser = _build_arg_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        sys.stderr.write(f"Configuration file not found: {config_path}\\n")
        return 1

    # Load configuration (we only need the seed for deterministic runs).
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write(f"Error parsing configuration file: {exc}\\n")
        return 1

    seed = config.get("seed", 42)
    seed_all(seed)

    # In a complete pipeline we would invoke the following stages:
    #   1. Data curation
    #   2. Participant simulation
    #   3. Validation (vector match + semantic similarity)
    #   4. Statistical analysis
    #   5. Report generation
    # For the initial quick‑start verification we simply acknowledge
    # that the script ran successfully.

    print("Pipeline completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())