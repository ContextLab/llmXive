"""Configuration module for the llmXive follow-up project.

Provides constants, dataset metadata, and a helper to assemble the
runtime configuration dictionary used by the pipeline entry point.
"""

import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Exit codes
# ----------------------------------------------------------------------
EXIT_CODE_SUCCESS = 0
EXIT_CODE_THROTTLING_FAILURE = 1

# ----------------------------------------------------------------------
# Default seed
# ----------------------------------------------------------------------
DEFAULT_SEED = 42

# ----------------------------------------------------------------------
# Dataset URLs (HuggingFace identifiers or repository names)
# ----------------------------------------------------------------------
# The identifiers must match the real datasets used in the benchmark.
DATASET_URLS = {
    "ms_marco": "microsoft/ms_marco",
    "spider": "xlangai/spider",
    # For the graph source we use a small, publicly‑available TTL file.
    # The URL points to a tiny RDF example that can be parsed by rdflib.
    "dbpedia_sample": "https://raw.githubusercontent.com/linkeddata/linkeddatahub/master/examples/example.ttl",
}

# ----------------------------------------------------------------------
# Dataset configuration details
# ----------------------------------------------------------------------
DATASET_CONFIGS = {
    "ms_marco": {
        "required_fields": ["text"],
        "max_samples": 1000,
        "config_name": "v1.1",
    },
    "spider": {
        # The test suite expects the field name ``question``.
        "required_fields": ["question"],
        "max_samples": 500,
        "config_name": None,
    },
    "dbpedia_sample": {
        "required_fields": ["entity"],
        # No HuggingFace config – we download the TTL directly.
        "max_samples": 300,
        "fallback": None,
    },
}

# ----------------------------------------------------------------------
# Synthetic fallback configuration (used only when the user explicitly
# requests it via ``--allow-synthetic``).  The default is **disabled**
# to satisfy the “no silent fallback” rule.
# ----------------------------------------------------------------------
SYNTHETIC_FALLBACK_CONFIG = {
    "enabled": False,
    "seed": 12345,
    "graph_nodes": 10,
    "graph_edges": 20,
}

# ----------------------------------------------------------------------
# Project root and common directories (absolute Paths)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = paths.data()          # <project>/data
RESULTS_DIR = paths.results()    # <project>/data/results

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_dataset_path(name: str) -> str:
    """Return the dataset URL/identifier for a given dataset name.

    Raises:
        KeyError: If the dataset name is not known.
    """
    try:
        return DATASET_URLS[name]
    except KeyError as exc:
        log.error("Dataset name '%s' not found in DATASET_URLS.", name)
        raise

def get_dataset_config(name: str) -> dict:
    """Return the configuration dictionary for a given dataset name.

    Raises:
        KeyError: If the dataset name is not known.
    """
    try:
        return DATASET_CONFIGS[name]
    except KeyError as exc:
        log.error("Dataset config for '%s' not found.", name)
        raise

def check_fallback_needed(name: str) -> bool:
    """Return True if the dataset configuration specifies a fallback."""
    config = DATASET_CONFIGS.get(name, {})
    return "fallback" in config and config["fallback"] is not None

def get_fallback_dataset(name: str) -> str | None:
    """Return the fallback dataset name if one is defined, else None."""
    config = DATASET_CONFIGS.get(name, {})
    return config.get("fallback")

def get_config() -> dict:
    """Assemble the runtime configuration dictionary.

    The dictionary is used by the main pipeline entry point and
    downstream components (e.g., throttling, fetchers).
    """
    # Seed can be overridden via environment variable LLMXIVE_SEED
    seed_env = os.getenv("LLMXIVE_SEED")
    try:
        seed = int(seed_env) if seed_env is not None else DEFAULT_SEED
    except ValueError:
        log.warning(
            "Invalid LLMXIVE_SEED='%s'; falling back to default seed %d.",
            seed_env,
            DEFAULT_SEED,
        )
        seed = DEFAULT_SEED

    config = {
        "seed": seed,
        "directories": {
            "raw": str(DATA_DIR / "raw"),
            "processed": str(DATA_DIR / "processed"),
            "results": str(RESULTS_DIR),
        },
        "throttling": {
            "cores": 2,
            "memory_gb": 7,
            "mode": "cgroups",
        },
    }
    return config

# Exported symbols for ``from config import *``
__all__ = [
    "EXIT_CODE_SUCCESS",
    "EXIT_CODE_THROTTLING_FAILURE",
    "DEFAULT_SEED",
    "DATASET_URLS",
    "DATASET_CONFIGS",
    "SYNTHETIC_FALLBACK_CONFIG",
    "PROJECT_ROOT",
    "DATA_DIR",
    "RESULTS_DIR",
    "get_dataset_path",
    "get_dataset_config",
    "check_fallback_needed",
    "get_fallback_dataset",
    "get_config",
]
