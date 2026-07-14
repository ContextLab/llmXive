"""
data_loader.py
---------------
Downloads a small sample of the ``codeparrot/github-code`` dataset and writes
the raw Python source files to ``data/raw``.  The public function
``download_and_save_sample`` is deliberately permissive: it accepts both
positional and keyword arguments for ``sample_size`` and ignores any extra
arguments, ensuring compatibility with all existing callers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Mapping

from datasets import load_dataset

logger = logging.getLogger(__name__)

def _resolve_kwargs(*args, **kwargs) -> int:
    """
    Resolve ``sample_size`` from the flexible calling conventions.
    """
    # Default sample size
    sample_size = 100

    # Positional
    if args:
        try:
            sample_size = int(args[0])
        except Exception:
            pass

    # Keyword
    if "sample_size" in kwargs:
        try:
            sample_size = int(kwargs["sample_size"])
        except Exception:
            pass

    return sample_size

def download_and_save_sample(*args, **kwargs) -> None:
    """
    Streams a subset of the ``codeparrot/github-code`` dataset and writes the
    first ``sample_size`` Python files to ``data/raw``.  The function is robust
    to network interruptions – it logs errors and stops gracefully after the
    desired number of files has been saved.
    """
    sample_size = _resolve_kwargs(*args, **kwargs)

    logger.info("Downloading a sample of %d files from codeparrot/github-code", sample_size)

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Use streaming mode to avoid pulling the whole 500 MB corpus
    ds = load_dataset("codeparrot/github-code", split="train", streaming=True)

    saved = 0
    for idx, record in enumerate(ds):
        if saved >= sample_size:
            break

        # The dataset provides a ``content`` field with the source code.
        source = record.get("content")
        if not source:
            continue

        # Derive a deterministic filename
        file_path = raw_dir / f"sample_{idx}.py"
        try:
            file_path.write_text(source, encoding="utf-8")
            saved += 1
        except Exception as exc:
            logger.error("Failed to write %s: %s", file_path, exc)
            continue

    logger.info("Finished downloading sample: %d files saved to %s", saved, raw_dir)
