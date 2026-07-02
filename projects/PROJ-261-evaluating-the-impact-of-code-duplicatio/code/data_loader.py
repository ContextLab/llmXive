from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

__all__ = ["stream_dataset", "download_and_save_sample"]


def stream_dataset(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
) -> Iterable[Dict[str, Any]]:
    """
    Thin wrapper around :func:`datasets.load_dataset` that yields examples
    from the requested split.  The function is kept separate so that unit
    tests can monkey‑patch it without pulling in the heavy ``datasets`` package.
    """
    from datasets import load_dataset

    ds = load_dataset(dataset_name, split=split, streaming=streaming)
    for example in ds:
        yield example


def download_and_save_sample(*args, **kwargs) -> None:
    """
    Download a *small* sample of the ``codeparrot/github-code`` dataset and
    write it to ``data/raw/github-code-sample.csv``.

    The function is deliberately permissive in its signature so that it can be
    invoked in any of the following ways without raising ``TypeError``:

    * ``download_and_save_sample()`` – uses defaults from ``code.config``.
    * ``download_and_save_sample(num_rows=500)`` – overrides the number of rows.
    * ``download_and_save_sample(path=Path(...))`` – custom output location.
    * ``download_and_save_sample(..., **kwargs)`` – any extra kwargs are ignored.

    Parameters
    ----------
    num_rows: int, optional
        Maximum number of rows to write.  Defaults to 1 000.
    path: pathlib.Path, optional
        Destination CSV file.  If omitted the default location derived from the
        configuration is used.
    """
    # Extract known optional arguments; ignore unknown ones.
    num_rows: int = kwargs.pop("num_rows", 1000)
    custom_path: Optional[Path] = kwargs.pop("path", None)

    # Pull defaults from the central config module.
    from code.config import get_dataset_name, get_streaming_enabled

    dataset_name = get_dataset_name()
    streaming = get_streaming_enabled()

    # Resolve the output path.
    if custom_path is None:
        # The dataset name contains a slash (e.g. "codeparrot/github-code").
        # Replace it with a dash for a filesystem‑friendly filename.
        safe_name = dataset_name.replace("/", "-")
        out_path = Path("data/raw") / f"{safe_name}-sample.csv"
    else:
        out_path = Path(custom_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Downloading a sample of %s (streaming=%s) – up to %d rows → %s",
        dataset_name,
        streaming,
        num_rows,
        out_path,
    )

    # Stream the dataset and write the requested number of rows.
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write a simple header – the exact columns are not critical for the MVP.
        writer.writerow(["id", "content"])

        for i, example in enumerate(stream_dataset(dataset_name, streaming=streaming)):
            if i >= num_rows:
                break
            # The dataset provides an ``id`` field and a ``content`` field containing
            # the raw source code.  Fallbacks are provided for robustness.
            row_id = example.get("id", i)
            content = example.get("content", "")
            writer.writerow([row_id, content])

    logger.info("Finished writing %d rows to %s", i + 1, out_path)
