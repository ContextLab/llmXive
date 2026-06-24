"""
download_qm9.py
----------------
Utility to download the QM9 dataset using the HuggingFace ``datasets`` library
and store it on disk in a format that downstream pipelines can consume.

The function is deliberately lightweight: it simply loads the ``train`` split
of the QM9 dataset and writes the Arrow-backed dataset to ``target_dir`` via
``Dataset.save_to_disk``.  This ensures that the dataset is cached locally and
can be re‑loaded without re‑downloading.

The implementation is used by the integration test ``test_qm9_download.py``.
"""

import os
from pathlib import Path
from typing import Union

from datasets import load_dataset

__all__ = ["download_qm9"]


def download_qm9(target_dir: Union[str, os.PathLike] = "data/raw/qm9") -> str:
    """
    Download the QM9 dataset and persist it to ``target_dir``.

    Parameters
    ----------
    target_dir: Union[str, Path]
        Directory where the dataset will be saved.  It will be created if it
        does not already exist.

    Returns
    -------
    str
        The absolute path to the directory containing the saved dataset.
    """
    # Resolve the target directory to an absolute path and ensure it exists
    target_path = Path(target_dir).expanduser().resolve()
    target_path.mkdir(parents=True, exist_ok=True)

    # Load the QM9 dataset (train split).  The HuggingFace ``datasets`` library
    # automatically handles downloading and caching.
    ds = load_dataset("qm9", split="train")

    # Persist the dataset to disk.  ``save_to_disk`` writes a directory
    # containing Arrow files and a metadata file.
    ds.save_to_disk(str(target_path))

    return str(target_path)
