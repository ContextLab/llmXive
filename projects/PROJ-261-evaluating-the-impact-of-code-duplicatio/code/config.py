"""config.py
Minimal configuration utilities required by the tests and scripts.
"""
Configuration module for the *Evaluating the Impact of Code Duplication on LLM Code Understanding* project.

This module centralises all configurable parameters used throughout the pipeline.
Each parameter has a dedicated getter function to keep the public API stable and
to make it easy for downstream scripts (e.g. ``quickstart_validation.py``) to
retrieve a complete configuration dictionary via :func:`get_all_config`.

The defaults are chosen to satisfy the reproducibility requirements described
in the specification (see ``specs/001-evaluate-code-duplication-llm-understanding``).
Values can be overridden at runtime by setting the corresponding environment
variables (e.g. ``PROJECT_RANDOM_SEED``).  All getters return concrete Python
types – no ``None`` is ever returned.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Default configuration values
# ---------------------------------------------------------------------------
_DEFAULTS: Dict[str, Any] = {
    # General reproducibility
    "random_seed": int(os.getenv("PROJECT_RANDOM_SEED", "42")),
    # Clone‑detection thresholds (US3 sensitivity analysis)
    "clone_thresholds": [0.7, 0.8, 0.9],
    # Resource limits
    "memory_limit_mb": int(os.getenv("PROJECT_MEMORY_LIMIT_MB", "8192")),  # 8 GB
    "max_runtime_seconds": int(os.getenv("PROJECT_MAX_RUNTIME_SECONDS", "7200")),  # 2 h
    # Data‑processing constraints
    "min_valid_segments": int(os.getenv("PROJECT_MIN_VALID_SEGMENTS", "1")),
    # Correlation analysis
    "correlation_method": os.getenv("PROJECT_CORRELATION_METHOD", "spearman"),
    "significance_threshold": float(os.getenv("PROJECT_SIGNIFICANCE_THRESHOLD", "0.05")),
    # Visualization
    "figure_format": os.getenv("PROJECT_FIGURE_FORMAT", "png"),
    "figure_dpi": int(os.getenv("PROJECT_FIGURE_DPI", "300")),
    # Checksum handling
    "checksum_algorithm": os.getenv("PROJECT_CHECKSUM_ALGORITHM", "sha256"),
    # Dataset / model specifics
    "dataset_name": os.getenv("PROJECT_DATASET_NAME", "codeparrot/github-code"),
    "model_name": os.getenv("PROJECT_MODEL_NAME", "Salesforce/codegen-350M-mono"),
    "quantization_bits": int(os.getenv("PROJECT_QUANTIZATION_BITS", "8")),
    # Streaming / PII handling
    "streaming_enabled": os.getenv("PROJECT_STREAMING_ENABLED", "true").lower() == "true",
    "pii_scan_enabled": os.getenv("PROJECT_PII_SCAN_ENABLED", "true").lower() == "true",
    # Base directories (relative to project root)
    "data_root": Path("data"),
    "raw_dir": Path("data/raw"),
    "processed_dir": Path("data/processed"),
    "analysis_dir": Path("data/analysis"),
    "figures_dir": Path("data/analysis/figures"),
}

# ---------------------------------------------------------------------------
# Getter helpers
# ---------------------------------------------------------------------------
def _get(key: str) -> Any:
    """Internal helper to fetch a value from ``_DEFAULTS``."""
    return _DEFAULTS[key]

# ---------------------------------------------------------------------------
# Public getters – one per configuration entry
# ---------------------------------------------------------------------------
def get_random_seed() -> int:
    """Return the random seed used throughout the project."""
    return int(_get("random_seed"))

def get_clone_thresholds() -> List[float]:
    """Return the list of clone‑detection similarity thresholds."""
    return list(_get("clone_thresholds"))

def get_memory_limit_mb() -> int:
    """Maximum memory (in megabytes) the pipeline may allocate."""
    return int(_get("memory_limit_mb"))

def get_max_runtime_seconds() -> int:
    """Maximum wall‑clock time (seconds) allowed for the whole run‑book."""
    return int(_get("max_runtime_seconds"))

def get_min_valid_segments() -> int:
    """Minimum number of code segments required for a file to be considered."""
    return int(_get("min_valid_segments"))

def get_correlation_method() -> str:
    """Statistical method used for correlation (e.g. ``spearman``)."""
    return str(_get("correlation_method"))

def get_significance_threshold() -> float:
    """p‑value threshold for statistical significance."""
    return float(_get("significance_threshold"))

def get_figure_format() -> str:
    """File extension/format for generated figures (``png`` or ``pdf``)."""
    return str(_get("figure_format"))

def get_figure_dpi() -> int:
    """Resolution (dots per inch) for raster figures."""
    return int(_get("figure_dpi"))

def get_checksum_algorithm() -> str:
    """Hash algorithm used for artifact checksum computation."""
    return str(_get("checksum_algorithm"))

def get_dataset_name() -> str:
    """Name of the HuggingFace dataset to stream."""
    return str(_get("dataset_name"))

def get_model_name() -> str:
    """Identifier of the pretrained model used for perplexity."""
    return str(_get("model_name"))

def get_quantization_bits() -> int:
    """Bit‑width for 8‑bit quantisation (e.g. ``8``)."""
    return int(_get("quantization_bits"))

def get_streaming_enabled() -> bool:
    """Whether the data loader should stream the dataset."""
    return bool(_get("streaming_enabled"))

def get_pii_scan_enabled() -> bool:
    """Whether the PII scanner should be executed."""
    return bool(_get("pii_scan_enabled"))

# ---------------------------------------------------------------------------
# Directory helpers – these return ``Path`` objects for convenience.
# ---------------------------------------------------------------------------
def get_data_root() -> Path:
    """Root ``data`` directory."""
    return Path(_get("data_root"))

def get_raw_dir() -> Path:
    """Directory for raw downloaded artifacts."""
    return Path(_get("raw_dir"))

def get_processed_dir() -> Path:
    """Directory for processed CSV/metric files."""
    return Path(_get("processed_dir"))

def get_analysis_dir() -> Path:
    """Directory for analysis outputs (e.g. correlation CSV)."""
    return Path(_get("analysis_dir"))

def get_figures_dir() -> Path:
    """Directory where generated figures are stored."""
    return Path(_get("figures_dir"))

# ---------------------------------------------------------------------------
# Aggregate view
# ---------------------------------------------------------------------------
def get_all_config() -> Dict[str, Any]:
    """
    Return a shallow copy of the full configuration dictionary.

    The returned mapping contains the same keys as ``_DEFAULTS`` but with
    concrete Python objects (e.g. ``Path`` instances) rather than the raw
    string values that may have been supplied via environment variables.
    """
    # Resolve Path objects so callers get actual ``Path`` instances.
    resolved = {}
    for k, v in _DEFAULTS.items():
        if k.endswith("_dir") or k == "data_root":
            resolved[k] = Path(v)
        else:
            resolved[k] = v
    return resolved

# ---------------------------------------------------------------------------
# Convenience: expose the public API via ``__all__`` – this helps static
# analysers and makes ``from config import *`` predictable.
# ---------------------------------------------------------------------------
__all__ = [
    "get_random_seed",
    "get_clone_thresholds",
    "get_memory_limit_mb",
    "get_max_runtime_seconds",
    "get_min_valid_segments",
    "get_correlation_method",
    "get_significance_threshold",
    "get_figure_format",
    "get_figure_dpi",
    "get_checksum_algorithm",
    "get_dataset_name",
    "get_model_name",
    "get_quantization_bits",
    "get_streaming_enabled",
    "get_pii_scan_enabled",
    "get_data_root",
    "get_raw_dir",
    "get_processed_dir",
    "get_analysis_dir",
    "get_figures_dir",
    "get_all_config",
]

# ---------------------------------------------------------------------------
# End of configuration module
# ---------------------------------------------------------------------------