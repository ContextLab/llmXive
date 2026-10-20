"""
create_layout.py
-----------------

Creates the project directory layout (``code/``, ``data/``, ``docs/``,
``tests/``, ``contracts/``, ``figures/``) and a minimal ``code/config.yaml``
if one does not already exist. Safe to re-run: existing files are never
overwritten.
"""

from pathlib import Path

import yaml

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

DIRECTORIES = [
    Path("code"),
    Path("code/data"),
    Path("code/models"),
    Path("code/analysis"),
    Path("code/utils"),
    Path("data"),
    Path("data/raw"),
    Path("data/processed"),
    Path("data/results"),
    Path("data/models"),
    Path("data/targets"),
    Path("docs"),
    Path("tests"),
    Path("contracts"),
    Path("figures"),
    Path("logs"),
]


def _ensure_dirs() -> None:
    """Create the main project directories."""
    for d in DIRECTORIES:
        d.mkdir(parents=True, exist_ok=True)
    log.info("Project directories ready: %s", ", ".join(str(d) for d in DIRECTORIES))


def _create_config() -> None:
    """Create a minimal configuration file if it does not exist."""
    config_path = paths.code("config.yaml")
    if config_path.exists():
        log.info("Config already exists at %s; leaving untouched", config_path)
        return
    cfg = {
        "active_dataset": None,
        "raw_csv_path": "data/raw/ctu13_scenario1.csv",
        "processed_dir": "data/processed",
        "results_dir": "data/results",
        "node_limit": 5000,
        "memory_limit_gb": 7,
        "seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    }
    with config_path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    log.info("Wrote minimal config to %s", config_path)


def main() -> None:
    """Entry point for the layout-creation script."""
    _ensure_dirs()
    _create_config()
    log.info("Project layout creation complete.")


if __name__ == "__main__":
    main()