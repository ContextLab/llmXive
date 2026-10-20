"""
Sampling Strategy
-----------------
Provides a deterministic subject‑sampling function that respects a
global random seed (set via ``utils.seed_manager``).  The function
returns a list of subject identifiers that can be used by downstream
preprocessing or simulation steps.
"""

import random
from pathlib import Path
from typing import List

from utils.seed_manager import get_seed, set_global_seed

def _list_subject_ids(bids_root: Path) -> List[str]:
    """
    Return a sorted list of subject identifiers (e.g. ``sub-01``) found
    under the BIDS root directory.
    """
    subjects = {p.name for p in bids_root.rglob("*") if p.is_dir() and p.name.startswith("sub-")}
    return sorted(subjects)


def sample_subjects(bids_root: Path, n: int, seed: int = None) -> List[str]:
    """
    Deterministically sample ``n`` subjects from ``bids_root``.
    If ``n`` exceeds the available number of subjects, the full list is
    returned and a warning is logged.

    Parameters
    ----------
    bids_root: Path
        Root of the extracted BIDS dataset.
    n: int
        Desired number of subjects.
    seed: int, optional
        Random seed; if omitted, the global seed set via
        ``set_global_seed`` is used.

    Returns
    -------
    List[str]
        List of sampled subject identifiers.
    """
    if seed is not None:
        set_global_seed(seed)
    elif get_seed() is not None:
        random.seed(get_seed())
    else:
        # If no seed has ever been set, fall back to system randomness
        random.seed()

    all_subjects = _list_subject_ids(bids_root)
    if n >= len(all_subjects):
        return all_subjects

    return random.sample(all_subjects, n)
