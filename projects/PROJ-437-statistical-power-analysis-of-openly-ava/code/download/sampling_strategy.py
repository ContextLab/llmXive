"""
Sampling Strategy
-----------------
Simple deterministic sampling of subject directories when the
requested sample size exceeds the available number of subjects.
The function respects a global random seed for reproducibility.
"""

import logging
import random
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def sample_subjects(
    subject_dirs: List[Path],
    target_n: int,
    seed: int | None = None,
) -> List[Path]:
    """
    Return a list of ``target_n`` subject directories sampled without
    replacement from ``subject_dirs``. If ``target_n`` exceeds the
    available subjects, the full list is returned and a warning is logged.

    Parameters
    ----------
    subject_dirs : List[Path]
        All available subject directories.
    target_n : int
        Desired number of subjects.
    seed : int | None, optional
        Random seed for reproducibility.

    Returns
    -------
    List[Path]
        Sampled subject directories.
    """
    if seed is not None:
        random.seed(seed)

    available = len(subject_dirs)
    if target_n >= available:
        logger.warning(
            f"Requested sample size {target_n} exceeds available subjects ({available}). "
            f"Returning all subjects."
        )
        return list(subject_dirs)

    sampled = random.sample(subject_dirs, target_n)
    logger.info(f"Sampled {target_n} subjects (out of {available}).")
    return sampled
