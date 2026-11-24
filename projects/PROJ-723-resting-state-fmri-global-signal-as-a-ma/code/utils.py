"""
Utility helpers for the Resting‑State fMRI Global Signal analysis pipeline.

This module provides a thin wrapper around common I/O and logging operations
used across the codebase. It deliberately avoids heavy dependencies and
keeps the implementation straightforward to ensure reliability in the
constrained CI environment.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from llmxive_toolkit import get_logger as llmxive_get_logger, paths

__all__ = [
    "get_logger",
    "setup_logging",
    "read_csv",
    "write_csv",
    "read_json",
    "write_json",
]


def get_logger(name: str) -> logging.Logger:
    """
    Return a project‑wide logger.

    The llmxive toolkit already provides a configurable logger; we simply
    expose it under the expected name.
    """
    return llmxive_get_logger(name)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger for scripts that are executed directly.

    This function is idempotent – calling it multiple times has no adverse
    effect because the ``logging.basicConfig`` call only configures the
    logger if it has no handlers attached.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# ----------------------------------------------------------------------
# CSV helpers
# ----------------------------------------------------------------------

def read_csv(path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file into a ``pandas.DataFrame``.

    Parameters
    ----------
    path: str or Path
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
    """
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    """
    Write a ``pandas.DataFrame`` to CSV, ensuring the parent directory exists.

    Parameters
    ----------
    df: pandas.DataFrame
        Dataframe to write.
    path: str or Path
        Destination file path.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


# ----------------------------------------------------------------------
# JSON helpers
# ----------------------------------------------------------------------

def read_json(path: str | Path) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    """
    Write a dictionary to a JSON file with pretty formatting.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
