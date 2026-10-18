"""Configuration helper utilities for the project.

The module reads ``code/config.yaml`` (or a user‑supplied path), validates
required sections, sets random seeds for reproducibility, and provides a
convenient ``get_dataset_paths`` function used by downstream scripts.
"""

import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Parameters
    ----------
    config_path : str or None
        Path to ``config.yaml``. If ``None`` the function looks for
        ``code/config.yaml`` relative to the project root.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    if config_path is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "code" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r") as f:
        return yaml.safe_load(f) or {}


def validate_config(config: Dict[str, Any]) -> None:
    """Validate that required sections exist in the configuration.

    Raises
    ------
    ValueError
        If a required key is missing.
    """
    required_sections = ["random_seeds", "paths"]
    for sec in required_sections:
        if sec not in config:
            raise ValueError(f"Missing required configuration section: '{sec}'")


def set_random_seeds(config: Dict[str, Any]) -> None:
    """Set random seeds for reproducibility across libraries.

    The ``random_seeds`` section may contain ``python``, ``numpy`` and
    ``torch`` keys. Missing keys are ignored.
    """
    seeds = config.get("random_seeds", {})
    py_seed = seeds.get("python")
    if py_seed is not None:
        random.seed(py_seed)

    try:
        import numpy as np
        np_seed = seeds.get("numpy")
        if np_seed is not None:
            np.random.seed(np_seed)
    except ImportError:
        pass  # NumPy is always available in the runner, but guard anyway.

    try:
        import torch
        torch_seed = seeds.get("torch")
        if torch_seed is not None:
            torch.manual_seed(torch_seed)
    except ImportError:
        pass  # Optional GPU support.


def ensure_paths_exist(config: Dict[str, Any]) -> None:
    """Create any directories declared in the ``paths`` section of the config."""
    paths = config.get("paths", {})
    for name, rel_path in paths.items():
        path_obj = Path(rel_path)
        path_obj.mkdir(parents=True, exist_ok=True)


def get_dataset_paths(config: Dict[str, Any], dataset_id: str) -> Dict[str, Path]:
    """Return a dictionary with common dataset file locations.

    Parameters
    ----------
    config : dict
        Loaded configuration dictionary.
    dataset_id : str
        GEO accession identifier (e.g. ``GSE136103``).

    Returns
    -------
    dict
        Keys ``raw``, ``processed`` and ``results`` mapping to absolute
        ``Path`` objects.
    """
    base = Path(config.get("paths", {}).get("data_root", "data"))
    return {
        "raw": base / "raw" / dataset_id,
        "processed": base / "processed" / dataset_id,
        "results": base / "results" / dataset_id,
    }
