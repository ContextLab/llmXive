"""
Deterministic seed‑pinning utilities for the llmXive project.

The original implementation provided ``set_seed`` and ``verify_seed``.
This updated version adds ``get_seed`` (required by T004) and
``generate_task_seed`` – a deterministic hash‑based mapping from a
task identifier to an integer seed.  All random libraries used by the
project are seeded through ``set_seed`` to satisfy the seed‑pinning
compliance checks.
"""

import hashlib
import random
from typing import Union

# ----------------------------------------------------------------------
# Helper: deterministic hash → int seed
# ----------------------------------------------------------------------
def generate_task_seed(task_id: Union[str, int]) -> int:
    """
    Produce a deterministic integer seed from ``task_id`` using SHA‑256.
    The resulting integer is limited to the 32‑bit range expected by the
    underlying random libraries.

    Parameters
    ----------
    task_id : str | int
        Identifier of the task (e.g. ``"T015a"`` or an integer).

    Returns
    -------
    int
        Deterministic seed value.
    """
    if isinstance(task_id, int):
        # Directly use the integer (already a seed) – keep within 32‑bit.
        return task_id & 0xFFFFFFFF
    # Convert to string, hash, and take the first 8 hex digits.
    hash_bytes = hashlib.sha256(str(task_id).encode("utf-8")).hexdigest()
    return int(hash_bytes[:8], 16)

# ----------------------------------------------------------------------
# Primary API
# ----------------------------------------------------------------------
def set_seed(task_id: Union[str, int]) -> None:
    """
    Pin the global RNGs (``random`` and ``numpy``) to a deterministic seed
    derived from ``task_id``.  All project code should call this function
    instead of using ``random.seed`` directly.

    Parameters
    ----------
    task_id : str | int
        Identifier used to derive the seed.
    """
    seed = generate_task_seed(task_id)
    random.seed(seed)
    try:
        # NumPy is always available in the execution environment.
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass  # NumPy not installed – nothing to seed.

def get_seed(task_id: Union[str, int]) -> int:
    """
    Return the deterministic integer seed associated with ``task_id``.
    This function is required by the unit test ``tests/unit/test_seeds.py``.

    Parameters
    ----------
    task_id : str | int
        Identifier of the task.

    Returns
    -------
    int
        Deterministic seed value.
    """
    return generate_task_seed(task_id)

def verify_seed(task_id: Union[str, int], expected_seed: int) -> bool:
    """
    Verify that the seed derived from ``task_id`` matches ``expected_seed``.
    This helper is used by internal validation scripts.

    Parameters
    ----------
    task_id : str | int
        Identifier of the task.
    expected_seed : int
        Seed value to compare against.

    Returns
    -------
    bool
        ``True`` if the derived seed equals ``expected_seed``.
    """
    return generate_task_seed(task_id) == expected_seed

# ----------------------------------------------------------------------
# Backwards‑compatible placeholder used by some legacy modules.
# ----------------------------------------------------------------------
def get_seed_state() -> dict:
    """
    Return a mapping of the current RNG state for debugging purposes.
    """
    state = {"random_state": random.getstate()}
    try:
        import numpy as np
        state["numpy_state"] = np.random.get_state()
    except ImportError:
        pass
    return state