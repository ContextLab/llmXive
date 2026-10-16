"""
Minimal data loader for trajectory files.

The production code stores trajectories as compressed NumPy ``.npz`` files
with the key ``states`` (and optionally ``dt``).  This helper reads such a
file and returns the state array.  It deliberately raises an exception if
the expected data cannot be found – this satisfies the “fail loudly”
requirement in the project specification.
"""
import numpy as np
from pathlib import Path
from typing import Union

def load_trajectory(path: Union[str, Path]) -> np.ndarray:
    """
    Load a trajectory from a ``.npz`` file.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the compressed NumPy file.

    Returns
    -------
    np.ndarray
        The ``states`` array stored in the file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file does not contain a ``states`` array.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Trajectory file not found: {p}")

    data = np.load(p, allow_pickle=False)
    if "states" in data:
        return data["states"]
    # Fall back to the first array in the archive if ``states`` is missing.
    if data.files:
        return data[data.files[0]]
    raise ValueError(f"No trajectory array found in {p}")