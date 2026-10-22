"""
Configuration Loader for the Corrosion Potential Prediction Pipeline.

This module focuses on loading the random seed configuration and applying
the seeds globally for reproducibility. It provides a simple API:

    load_and_set_seeds() -> int
        Loads ``config/seeds.yaml`` (or a custom path) and sets
        ``numpy.random.seed``, ``random.seed`` and, if available,
        ``torch.manual_seed`` to the configured integer seed.

The function is executed on import so that any module importing
``code.utils.config_loader`` automatically benefits from a deterministic
random state.

The original, more generic configuration utilities have been retained
(they are not used by the current pipeline) but their imports have been
corrected to use relative paths.
"""

import random
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml

# Relative imports – the utils package lives in ``code/utils``.
from .logging import get_logger
from .exceptions import DataInsufficientError, CorrosionPipelineError

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Generic YAML loader (kept for possible future extensions)
# ----------------------------------------------------------------------
def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        config_path: Path to the YAML file (relative to the project root).

    Returns:
        Dictionary containing the configuration.

    Raises:
        CorrosionPipelineError: If the file cannot be read or parsed.
    """
    full_path = Path(config_path)

    if not full_path.exists():
        raise CorrosionPipelineError(f"Configuration file not found: {config_path}")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            raise CorrosionPipelineError(f"Configuration file is empty: {config_path}")

        return config

    except yaml.YAMLError as e:
        raise CorrosionPipelineError(f"Failed to parse YAML config {config_path}: {e}")
    except IOError as e:
        raise CorrosionPipelineError(f"Failed to read config file {config_path}: {e}")

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------
GLOBAL_SEED: int | None = None  # exposed for downstream checks / tests

def _extract_seed_from_config(cfg: Dict[str, Any]) -> int:
    """
    Extract the integer seed from the supplied configuration dictionary.

    The project historically used two possible layouts:
    1. ``{'random_seed': 42}``
    2. ``{'seeds': {'global_seed': 42, ...}}``

    This helper normalises both formats.

    Raises:
        DataInsufficientError: If no suitable integer seed is found.
    """
    # Layout 1 – flat key
    if "random_seed" in cfg:
        seed = cfg["random_seed"]
    # Layout 2 – nested under ``seeds`` (backwards‑compatible)
    elif "seeds" in cfg and isinstance(cfg["seeds"], dict):
        seed = cfg["seeds"].get("global_seed")
    else:
        raise DataInsufficientError("Seeds configuration missing required key")

    if not isinstance(seed, int):
        raise DataInsufficientError(
            f"Seed value must be an integer, got {type(seed).__name__}"
        )
    return seed

def _apply_global_seeds(seed: int) -> None:
    """
    Set the global random state for the standard libraries used in the pipeline.

    Args:
        seed: Integer seed to apply.
    """
    random.seed(seed)
    np.random.seed(seed)

    # torch is optional – the pipeline must work without it.
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        # No torch available; silently ignore – the test suite will
        # simply skip the torch‑specific assertion.
        pass

def load_and_set_seeds(config_path: str = "config/seeds.yaml") -> int:
    """
    Load the seed configuration file and set the global random seeds.

    The function logs the operation and stores the seed in the module‑level
    ``GLOBAL_SEED`` variable for external inspection (e.g. unit tests).

    Args:
        config_path: Relative path to the YAML seed file.

    Returns:
        The integer seed that was applied.

    Raises:
        DataInsufficientError: If the configuration cannot be parsed or
                                does not contain a valid integer seed.
        CorrosionPipelineError: If the file cannot be read.
    """
    cfg = load_yaml_config(config_path)
    seed = _extract_seed_from_config(cfg)
    _apply_global_seeds(seed)

    global GLOBAL_SEED
    GLOBAL_SEED = seed

    logger.info(f"Global random seed set to {seed}")
    return seed

# ----------------------------------------------------------------------
# Backwards‑compatible validation helpers (kept for other scripts)
# ----------------------------------------------------------------------
def validate_seeds_config(config: Dict[str, Any]) -> None:
    """
    Validate the seeds configuration.

    This function is retained for compatibility with older scripts that
    may still import it. It simply forwards to the newer extraction logic.
    """
    _extract_seed_from_config(config)  # will raise if invalid
    logger.info("Seeds configuration validated successfully")

def verify_all_keys_exist(config: Dict[str, Any], section: str) -> bool:
    """
    Verify that a section in the config is non‑empty.

    Args:
        config: The configuration dictionary.
        section: The section key to check.

    Returns:
        True if the section exists and is non‑empty.

    Raises:
        DataInsufficientError: If the section is missing or empty.
    """
    if section not in config:
        raise DataInsufficientError(f"Configuration section '{section}' is missing")

    section_data = config[section]

    if isinstance(section_data, dict) and len(section_data) == 0:
        raise DataInsufficientError(f"Configuration section '{section}' is empty")
    if isinstance(section_data, list) and len(section_data) == 0:
        raise DataInsufficientError(f"Configuration section '{section}' is empty")
    if section_data is None:
        raise DataInsufficientError(f"Configuration section '{section}' is None")

    return True

# ----------------------------------------------------------------------
# Initialise seeds on import so that any script importing this module
# automatically benefits from deterministic behaviour.
# ----------------------------------------------------------------------
try:
    load_and_set_seeds()
except Exception as exc:
    # Importing the module should never crash the entire pipeline – we log
    # the error and allow the caller to handle it if necessary.
    logger.error(f"Failed to initialise global seeds: {exc}")
