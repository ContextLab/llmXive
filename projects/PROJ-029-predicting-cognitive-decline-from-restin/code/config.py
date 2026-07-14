"""Configuration management for the project.

This module centralises environment configuration such as the global random
seed and the maximum allowed runtime for any long‑running script.  All
pipeline scripts should import and invoke the helper functions defined here
at the very start of their execution.

The configuration values are read from ``data/config.json`` if the file
exists; otherwise sensible defaults are used:

- ``random_seed``: 42
- ``max_runtime_seconds``: 6 hours (21600 s)

The module provides three public helpers:

* :func:`load_config` – Load the JSON configuration file.
* :func:`apply_random_seed` – Set the random seed for ``random``,
  ``numpy`` and, if available, ``torch`` and ``tensorflow``.
* :func:`enforce_runtime_limit`` – Install a watchdog that raises
  :class:`RuntimeError` if the process exceeds the configured time limit.

The implementation is deliberately lightweight and has no external
dependencies beyond the Python standard library and ``numpy`` (which is
already a project requirement).  It is safe to import on any platform;
the timeout watchdog falls back to a simple time‑check on platforms that
do not support ``signal.SIGALRM`` (e.g. Windows).
"""

from __future__ import annotations

import json
import os
import random
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np

# ----------------------------------------------------------------------
# Default configuration values – used when ``data/config.json`` is absent.
# ----------------------------------------------------------------------
DEFAULT_CONFIG: Dict[str, Any] = {
    "random_seed": 42,
    "max_runtime_seconds": 6 * 60 * 60,  # 6 hours
}

CONFIG_PATH = Path(__file__).parents[1] / "data" / "config.json"


def _read_json_config(path: Path) -> Dict[str, Any]:
    """Read a JSON file and return a dict.

    Parameters
    ----------
    path: Path
        Path to the JSON configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in configuration file {path}: {exc}") from exc


def load_config() -> Dict[str, Any]:
    """Load the project configuration.

    Returns
    -------
    dict
        Configuration dictionary containing at least ``random_seed`` and
        ``max_runtime_seconds``. Missing keys are filled with defaults.
    """
    cfg = _read_json_config(CONFIG_PATH)
    # Merge with defaults – user‑provided values override defaults.
    merged = {**DEFAULT_CONFIG, **cfg}
    return merged


def apply_random_seed(seed: int | None = None) -> None:
    """Set the global random seed for reproducibility.

    This function sets the seed for the Python ``random`` module,
    ``numpy`` and, if the optional libraries ``torch`` or ``tensorflow`` are
    installed, for those as well.  The seed used is taken from the
    configuration file unless an explicit ``seed`` argument is supplied.

    Parameters
    ----------
    seed: int | None
        Optional explicit seed.  If ``None`` the value from
        :func:`load_config` is used.
    """
    cfg = load_config()
    chosen_seed = seed if seed is not None else cfg.get("random_seed", 42)

    # Standard library and numpy
    random.seed(chosen_seed)
    np.random.seed(chosen_seed)

    # Ensure deterministic hashing (important for some pandas operations)
    os.environ["PYTHONHASHSEED"] = str(chosen_seed)

    # Optional deep‑learning libraries – import lazily so they remain optional
    try:
        import torch

        torch.manual_seed(chosen_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(chosen_seed)
    except Exception:
        # Torch not installed or failed to set seed – silently ignore.
        pass

    try:
        import tensorflow as tf

        tf.random.set_seed(chosen_seed)
    except Exception:
        # TensorFlow not installed – ignore.
        pass


class _RuntimeWatchdog(threading.Thread):
    """Background thread that aborts the process after a timeout."""

    def __init__(self, timeout_seconds: int):
        super().__init__(daemon=True)
        self.timeout_seconds = timeout_seconds
        self.start_time = time.time()
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout_seconds:
                # Raising in the main thread is not possible from a daemon;
                # we terminate the process with a clear error message.
                sys.stderr.write(
                    f"\n[RuntimeLimit] Exceeded maximum runtime of {self.timeout_seconds} seconds "
                    f"(elapsed {int(elapsed)} s). Terminating.\n"
                )
                os._exit(1)
            time.sleep(1)

    def stop(self) -> None:
        self._stop_event.set()


def enforce_runtime_limit(limit_seconds: int | None = None) -> _RuntimeWatchdog:
    """Enforce a maximum runtime for the current process.

    A background watchdog thread is started; if the process runs longer than
    the allowed limit it will terminate with exit code ``1``.  The function
    returns the watchdog object so callers can optionally stop it early
    (e.g. after successful completion).

    Parameters
    ----------
    limit_seconds: int | None
        Maximum allowed runtime in seconds.  If ``None`` the value from the
        configuration file is used.

    Returns
    -------
    _RuntimeWatchdog
        The started watchdog thread.
    """
    cfg = load_config()
    max_seconds = limit_seconds if limit_seconds is not None else cfg.get(
        "max_runtime_seconds", 6 * 60 * 60
    )
    watchdog = _RuntimeWatchdog(int(max_seconds))
    watchdog.start()
    return watchdog


# ----------------------------------------------------------------------
# Convenience entry‑point used by many scripts
# ----------------------------------------------------------------------
def initialise_environment() -> _RuntimeWatchdog:
    """Apply the global seed and start the runtime watchdog.

    Most pipeline scripts can simply call ``initialise_environment()`` at the
    top of their ``main()`` implementation:

    .. code-block:: python

        from config import initialise_environment

        def main():
            watchdog = initialise_environment()
            # … script logic …
            watchdog.stop()

    Returns
    -------
    _RuntimeWatchdog
        The started watchdog thread (already running).
    """
    apply_random_seed()
    return enforce_runtime_limit()
