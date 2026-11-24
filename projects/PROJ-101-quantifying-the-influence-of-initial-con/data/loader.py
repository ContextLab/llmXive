"""
Simple loader for trajectory files saved as ``.npz`` archives.
The loader returns a dictionary mirroring the structure used by the
test suite (``{'states': <np.ndarray>, 'dt': <float>}``).
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Dict, Any


def load_trajectory(path: str | Path) -> Dict[str, Any]:
    """
    Load a trajectory stored with ``np.savez_compressed``.

    The file must contain at least the keys ``'states'`` (the state matrix)
    and ``'dt'`` (the time step).  The function returns a plain dictionary
    so that the downstream code can treat it uniformly whether the data
    originated from disk or from a mock in the test suite.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the ``.npz`` file.

    Returns
    -------
    dict
        ``{'states': <np.ndarray>, 'dt': <float>}``
    """
    npz_path = Path(path)
    with np.load(npz_path) as data:
        states = data["states"]
        dt = float(data["dt"])
    return {"states": states, "dt": dt}
