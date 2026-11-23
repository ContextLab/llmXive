"""
Configuration loader for the ball milling impact prediction project.

This module provides a single public function :func:`load_config` that reads the
YAML configuration file ``src/config/config.yaml`` and returns its contents as a
dictionary.  It validates that the top‑level sections required by the
specification (``api``, ``gpr_max_runtime``, ``gpr_max_memory``, and ``ocr``)
are present and raises a clear ``KeyError`` if any are missing.

The loader uses the ``llmxive_toolkit.paths`` helper to locate the configuration
file relative to the project root, ensuring the same behaviour across all
scripts and test environments.
"""

from pathlib import Path
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Path to the configuration YAML file. ``paths.config`` creates a Path inside the
# ``config`` top‑level folder and ensures the parent directory exists.
_CONFIG_PATH: Path = paths.config("config.yaml")


def _validate_config_structure(config: dict) -> None:
    """
    Validate that the loaded configuration contains the required top‑level keys.

    Parameters
    ----------
    config: dict
        The parsed YAML configuration.

    Raises
    ------
    KeyError
        If any required key is missing.
    """
    required_top_keys = {"api", "gpr_max_runtime", "gpr_max_memory", "ocr"}
    missing = required_top_keys - set(config.keys())
    if missing:
        raise KeyError(
            f"Configuration file {_CONFIG_PATH} is missing required keys: {', '.join(sorted(missing))}"
        )

    # Validate that the ``api`` section contains the expected sub‑sections.
    api_required = {"materials_project", "nist", "arxiv"}
    api_section = config.get("api", {})
    missing_api = api_required - set(api_section.keys())
    if missing_api:
        raise KeyError(
            f"The 'api' section must contain {', '.join(sorted(api_required))} entries; missing: {', '.join(sorted(missing_api))}"
        )

    # OCR section must contain ``fallback_enabled`` (boolean) and ``language`` (list)
    ocr_section = config.get("ocr", {})
    if not isinstance(ocr_section.get("fallback_enabled"), bool):
        raise KeyError("OCR configuration requires a boolean 'fallback_enabled' flag.")
    if not isinstance(ocr_section.get("language"), list):
        raise KeyError("OCR configuration requires a list 'language' entry.")


def load_config() -> dict:
    """
    Load and return the project's configuration.

    Returns
    -------
    dict
        The configuration dictionary parsed from ``src/config/config.yaml``.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    yaml.YAMLError
        If the file cannot be parsed as valid YAML.
    KeyError
        If required configuration keys are missing.
    """
    if not _CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at {_CONFIG_PATH}")

    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        log.error("Failed to parse configuration YAML: %s", exc)
        raise

    if not isinstance(config, dict):
        raise yaml.YAMLError("Root of configuration YAML must be a mapping/dictionary.")

    # Validate required structure
    _validate_config_structure(config)

    log.debug("Configuration loaded successfully from %s", _CONFIG_PATH)
    return config