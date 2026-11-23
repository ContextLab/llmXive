import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# -------------------------------------------------------------------------
# Global configuration constants
# -------------------------------------------------------------------------

# Random seed for reproducibility across the entire pipeline.
# All modules that require deterministic behavior should import this.
RANDOM_SEED: int = 42

# Hyperparameters used by various components of the pipeline.
# These can be extended as needed by downstream tasks.
HYPERPARAMETERS: Dict[str, Any] = {
    # Example hyperparameters – can be overridden in downstream scripts
    "learning_rate": 0.01,
    "n_estimators": 100,
    "max_depth": None,
    "cv_folds": 5,
}

# Whitelist of validated data source URLs (Materials Project and OQMD).
# Used by validators.validate_citations to ensure provenance compliance.
VALIDATED_SOURCE_WHITELIST: List[str] = [
    "https://materialsproject.org",
    "https://oqmd.org",
]

# -------------------------------------------------------------------------
# Helper functions for project layout
# -------------------------------------------------------------------------

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project is structured as:
    projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
        code/
        data/
        ...
    This function looks for the 'code' directory relative to the current file.
    """
    # Resolve this file's location and step up to the project root.
    current_file_path = Path(__file__).resolve()
    code_dir = current_file_path.parent
    project_root = code_dir.parent

    # Verify the expected sub‑directories exist; if not, we simply return
    # the inferred root (the calling code will handle missing dirs).
    expected_dirs = ["data", "results", "tests"]
    for d in expected_dirs:
        if not (project_root / d).exists():
            # The directory may not exist yet during early setup phases.
            # No exception is raised here to keep the function side‑effect free.
            pass

    return project_root


def get_data_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of key data paths used throughout the pipeline.
    Keys:
        - raw:       Path to raw downloaded data.
        - processed: Path to processed data products.
        - potentials: Path where interatomic potentials are stored.
        - metadata: Path to the metadata.yaml provenance file.
    """
    root = get_project_root()
    return {
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "potentials": root / "data" / "potentials",
        "metadata": root / "data" / "metadata.yaml",
    }


def get_config_summary() -> Dict[str, Any]:
    """
    Returns a concise summary of the current configuration state.
    This is useful for logging, debugging, or snapshotting the
    configuration to disk.
    """
    return {
        "project_root": str(get_project_root()),
        "data_paths": {k: str(v) for k, v in get_data_paths().items()},
        "random_seed": RANDOM_SEED,
        "hyperparameters": HYPERPARAMETERS,
        "validated_source_whitelist": VALIDATED_SOURCE_WHITELIST,
    }


def save_config_snapshot(output_path: Optional[Path] = None) -> Path:
    """
    Persists the current configuration summary to a JSON file.

    Parameters
    ----------
    output_path : Optional[Path]
        Destination for the snapshot. If None, defaults to
        ``<project_root>/results/config_snapshot.json``.

    Returns
    -------
    Path
        The path to the written JSON file.
    """
    if output_path is None:
        output_path = get_project_root() / "results" / "config_snapshot.json"

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = get_config_summary()
    # Add a timestamp for provenance (ISO‑8601 format).
    config["timestamp"] = "2023-10-27T10:00:00Z"  # Placeholder; can be replaced by callers.

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return output_path


# Exported symbols for ``from config import *``
__all__ = [
    "RANDOM_SEED",
    "HYPERPARAMETERS",
    "VALIDATED_SOURCE_WHITELIST",
    "get_project_root",
    "get_data_paths",
    "get_config_summary",
    "save_config_snapshot",
]