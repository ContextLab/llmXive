"""
Configuration module for the project.

Provides:
- Hyperparameters dataclass with default random seed.
- ensure_directories(): creates the required project directory hierarchy (excluding platform‑owned `state/`).
- get_config_summary(): returns a summary dictionary of hyperparameters and
  absolute paths of the created directories.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any

# The llmxive toolkit provides convenient helpers for standard project folders.
# Importing it here avoids hard‑coding relative paths and guarantees that the
# folders are created inside the repository root.
from llmxive_toolkit import paths

@dataclass
class Hyperparameters:
    """
    Global hyper‑parameters and constants used throughout the pipeline.
    """
    random_seed: int = 42
    # Additional hyper‑parameters can be added here as the project evolves.
    # Example placeholders:
    # learning_rate: float = 0.01
    # n_estimators: int = 100

def ensure_directories() -> None:
    """
    Create all required top‑level project directories if they do not already exist.

    The required hierarchy (relative to the project root) excludes the
    platform‑owned ``state/`` directory, which is managed by the execution
    environment.

    - data/raw/
    - data/derived/
    - code/
    - tests/
    - docs/
    - contracts/
    - results/
    """
    # Using the toolkit's path helpers guarantees folder creation.
    required_dirs = [
        paths.data("raw"),
        paths.data("derived"),
        paths.code(),
        paths.tests(),
        paths.docs(),
        paths.contracts(),
        paths.results(),
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """
    Return a dictionary summarising the current configuration.

    Includes the hyper‑parameter values and the absolute paths of the
    directories created by ``ensure_directories``.
    """
    hp = Hyperparameters()
    summary = {
        "hyperparameters": asdict(hp),
        "directories": {
            "data_raw": str(paths.data("raw")),
            "data_derived": str(paths.data("derived")),
            "code": str(paths.code()),
            "tests": str(paths.tests()),
            "docs": str(paths.docs()),
            "contracts": str(paths.contracts()),
            "results": str(paths.results()),
        },
    }
    return summary
