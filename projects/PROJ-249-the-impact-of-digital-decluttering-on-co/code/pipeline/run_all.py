"""
Run All Pipeline – Setup Stage (T001)

This script implements the minimal end‑to‑end pipeline required for
task T001. It validates the study configuration, ensures that all
required project directories exist, and writes a deterministic log
file that ends with the required ``STATUS: SUCCESS`` line.  The
implementation avoids importing any of the downstream analysis or
compliance modules that are not yet implemented, thereby guaranteeing
that the command

    python -m code.pipeline.run_all --config code/config/study_config.yaml

completes without error on a fresh checkout.

The script is also importable (e.g. ``from code.pipeline.run_all import
main``) and can be used by later pipeline stages.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

import yaml
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create all directories required by the study layout.

    The list mirrors the layout described in the specification and
    quickstart documentation.
    """
    required_dirs = [
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
    for d in required_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def load_config(config_path: str) -> dict:
    """
    Load and minimally validate the YAML configuration file.

    Parameters
    ----------
    config_path: str
        Path to the configuration YAML.

    Returns
    -------
    dict
        Parsed configuration dictionary.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed.
    """
    cfg_path = Path(config_path)
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Configuration file must contain a YAML mapping.")
    log.debug(f"Loaded configuration from {config_path}")
    return config

def write_pipeline_log() -> None:
    """
    Append a timestamped entry to ``results/pipeline.log`` and finish
    with the required ``STATUS: SUCCESS`` line.
    """
    log_path = Path("results/pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as f:
        now = datetime.utcnow().isoformat()
        f.write(f"{now} - INFO - Pipeline setup completed\\n")
        f.write("STATUS: SUCCESS\\n")
    log.info(f"Wrote pipeline log to {log_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    """
    Execute the minimal pipeline.

    Parameters
    ----------
    argv : list | None
        Argument list; if ``None`` the arguments from ``sys.argv`` are used.

    Returns
    -------
    int
        Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Run the full study pipeline (setup stage only)."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the study configuration YAML file.",
    )
    args = parser.parse_args(argv)

    # 1. Load and validate configuration
    _ = load_config(args.config)

    # 2. Ensure required directory layout exists
    ensure_directories()

    # 3. Write deterministic pipeline log
    write_pipeline_log()

    print("Pipeline setup completed successfully. STATUS: SUCCESS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
