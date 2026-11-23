"""
Configuration module for the project.
Provides a mutable mapping that supports both dict-style and attribute-style access.
"""
import os
from pathlib import Path
from typing import Any, Dict

class Config(dict):
    """
    A dict subclass that also allows attribute access.
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(name) from e

_default_config = Config({
    # Core hyper‑parameters (can be overridden via CLI)
    "W_LIST": [0.5, 1.0, 2.0],
    "L_LIST": [100, 200, 400, 800, 1600],
    "NUM_REALIZATIONS": 100,
    "SEED": 42,
    "WEAK_DISORDER_CUTOFF": 1.0,
    "NUMERICAL_RESIDUAL_THRESHOLD": 1e-6,
    "MAX_TM_ITERATIONS": 10000,
    # Directory layout (mirrors llmxive_toolkit.paths helpers)
    "DATA_DIR": "data",
    "DATA_METADATA": os.path.join("data", "metadata"),
    "DATA_PROCESSED": os.path.join("data", "processed"),
    "DATA_RAW": os.path.join("data", "raw"),
})

def get_config() -> Config:
    """
    Return a mutable configuration object.

    The returned object behaves like a dict (e.g. config[\"W_LIST\"])
    and also like an object with attributes (e.g. config.W_LIST).
    """
    return _default_config
