"""
data_loader.py
----------------
Downloads a small sample from the ``codeparrot/github-code`` dataset using the
``datasets`` library in streaming mode and writes a CSV suitable for downstream
processing.
The public function ``download_and_save_sample`` now accepts flexible arguments
(both positional and keyword) to satisfy all callers.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from datasets import load_dataset

logger = logging.getLogger(__name__)

_DEFAULT_DATASET = "codeparrot/github-code"
_DEFAULT_SAMPLE_SIZE = 100
_RAW_OUTPUT_PATH = Path("data/raw/github-code-sample.csv")


def _stream_dataset(sample_size: int) -> Iterable[dict]:
    """
    Stream the dataset and yield the first ``sample_size`` examples.
    Each yielded dict contains at least a ``content`` field with the raw code.
    """
    ds = load_dataset(_DEFAULT_DATASET, split="train", streaming=True)
    for i, example in enumerate(ds):
        if i >= sample_size:
            break
        # The dataset schema uses the key ``content`` for the source code.
        yield {"code": example.get("content", "")}


def download_and_save_sample(*args, **kwargs) -> None:
    """
    Download a modest sample of the code corpus and write it to CSV.
    
    Accepted signatures:
    
    * ``download_and_save_sample(sample_size=100)`` – keyword argument.
    * ``download_and_save_sample(200)`` – positional argument interpreted as
      ``sample_size``.
    * ``download_and_save_sample()`` – uses the default size.
    
    Parameters
    ----------
    sample_size : int, optional
        Number of examples to download. Defaults to 100.
    output_path : pathlib.Path, optional
        Destination CSV path. Defaults to ``data/raw/github-code-sample.csv``.
    """
    # Resolve arguments
    sample_size = _DEFAULT_SAMPLE_SIZE
    output_path = _RAW_OUTPUT_PATH

    if args:
        if isinstance(args[0], int):
            sample_size = args[0]
    if "sample_size" in kwargs:
        sample_size = int(kwargs["sample_size"])

    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    logger.info("Downloading %d examples from %s → %s", sample_size, _DEFAULT_DATASET, output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code"])
        writer.writeheader()
        for record in _stream_dataset(sample_size):
            writer.writerow(record)

    logger.info("Sample saved to %s", output_path)
