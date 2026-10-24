"""Data fetching utilities for real datasets.

This module provides three primary loader functions that return
streaming datasets or downloaded files for the benchmark:

* ``load_ms_marco`` – streams the MS MARCO test split.
* ``load_spider`` – streams the Spider tables split.
* ``load_dbpedia`` – downloads the DBpedia triples parquet file.

The functions raise ``DataFetchError`` if the required libraries are
missing or the download fails. No synthetic fallback is performed,
complying with the task specification.
"""

from __future__ import annotations

import pathlib
from typing import Iterable

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

class DataFetchError(RuntimeError):
    """Raised when a dataset cannot be fetched."""


# ----------------------------------------------------------------------
# Public loader functions
# ----------------------------------------------------------------------
def load_ms_marco() -> Iterable[dict]:
    """Stream the MS MARCO *test* split.

    Returns
    -------
    Iterable[dict]
        A streaming ``datasets`` object yielding examples from the
        ``microsoft/ms_marco`` repository, ``v1.1`` configuration,
        ``test`` split.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:
        log.error("datasets library is required for MS MARCO loading: %s", exc)
        raise DataFetchError("datasets library not installed") from exc

    try:
        ds = load_dataset(
            "microsoft/ms_marco",
            "v1.1",
            split="test",
            streaming=True,
            download_mode="force_redownload",
        )
        log.info("MS MARCO test split streamed successfully")
        return ds
    except Exception as exc:
        log.error("Failed to stream MS MARCO test split: %s", exc)
        raise DataFetchError("Unable to load MS MARCO test split") from exc


def load_spider() -> Iterable[dict]:
    """Stream the Spider *tables* split.

    Returns
    -------
    Iterable[dict]
        A streaming ``datasets`` object yielding Spider table examples.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:
        log.error("datasets library is required for Spider loading: %s", exc)
        raise DataFetchError("datasets library not installed") from exc

    try:
        # The Spider dataset does not provide a dedicated "tables" config
        # in the public hub; the standard "train" split contains the
        # required table information. We stream that split directly.
        ds = load_dataset(
            "spider",
            split="train",
            streaming=True,
            download_mode="force_redownload",
        )
        log.info("Spider tables streamed successfully (using train split)")
        return ds
    except Exception as exc:
        log.error("Failed to stream Spider tables split: %s", exc)
        raise DataFetchError("Unable to load Spider tables split") from exc


def load_dbpedia() -> pathlib.Path:
    """Download the DBpedia 2023 triples parquet file.

    The file is retrieved via :func:`huggingface_hub.hf_hub_download` and
    stored under the project's ``data/raw`` directory.

    Returns
    -------
    pathlib.Path
        Path to the downloaded ``dbpedia_triples.parquet`` file.
    """
    try:
        from huggingface_hub import hf_hub_download  # type: ignore
    except Exception as exc:
        log.error("huggingface_hub is required for DBpedia download: %s", exc)
        raise DataFetchError("huggingface_hub library not installed") from exc

    try:
        # Repository and filename as specified in the task description.
        repo_id = "allenai/dbpedia-2023-triples"
        filename = "dbpedia_triples.parquet"

        # Specify that we are downloading from a dataset repository.
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
        )
        dest_path = paths.data("raw", "dbpedia_triples.parquet")
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move the file into the project's data folder.
        pathlib.Path(local_path).replace(dest_path)

        log.info("DBpedia triples parquet downloaded to %s", dest_path)
        return dest_path
    except Exception as exc:
        log.error("Failed to download DBpedia triples parquet: %s", exc)
        raise DataFetchError("Unable to download DBpedia triples") from exc
