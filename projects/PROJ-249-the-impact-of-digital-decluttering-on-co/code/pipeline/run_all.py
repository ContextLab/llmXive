"""
run_all.py

Entry point that creates the required project layout, validates the
configuration file and writes a minimal pipeline log.  This script is
deliberately lightweight – it performs only the actions required for
task T001 (layout creation) and the integration test
``tests/integration/test_layout.py``.
"""

import argparse
import sys
import yaml
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Required configuration keys (as asserted by the integration test)
# ----------------------------------------------------------------------
REQUIRED_KEYS = {
    "seed",
    "n_participants",
    "dropout_rate",
    "effect_sizes",
    "practice_effect_grid",
    "bootstrap_resamples",
    "start_date",
    "pilot_n",
    "tasks",
}

# ----------------------------------------------------------------------
# Required top‑level directories (relative to the project root)
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
    "code/scoring",
    "code/analysis",
    "code/compliance",
    "code/viz",
    "code/validation",
    "code/pipeline",
    "code/tests",
    "data/raw",
    "data/processed",
    "data/results",
    "figures",
]

# ----------------------------------------------------------------------
# Helper: load and validate the YAML configuration
# ----------------------------------------------------------------------
def load_and_validate_config(config_path: Path) -> dict:
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    missing = REQUIRED_KEYS - set(cfg.keys())
    if missing:
        raise ValueError(f"missing required keys: {', '.join(sorted(missing))}")

    # Basic sanity checks (e.g., effect_sizes must contain the expected metrics)
    expected_metrics = {"SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"}
    if set(cfg["effect_sizes"].keys()) != expected_metrics:
        raise ValueError(
            "effect_sizes must contain exactly the metrics: "
            f"{', '.join(sorted(expected_metrics))}"
        )
    return cfg

# ----------------------------------------------------------------------
# Helper: create all required directories under the (monkey‑patched) root
# ----------------------------------------------------------------------
def create_required_dirs(root: Path) -> None:
    for rel in REQUIRED_DIRS:
        dir_path = root / rel
        dir_path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Created directory: {dir_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create project layout and validate configuration."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the study configuration YAML file.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).resolve()
    try:
        cfg = load_and_validate_config(config_path)
    except Exception as exc:
        log.error(f"Configuration validation failed: {exc}")
        return 1

    # Ensure all required directories exist relative to the project root.
    # ``paths.root`` may have been monkey‑patched by the test suite.
    create_required_dirs(paths.root)

    # Write a minimal pipeline log to indicate success.
    log_path = paths.results("pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write("Pipeline layout creation completed.\n")
        f.write("STATUS: SUCCESS\n")

    log.info(f"Layout created and configuration validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
