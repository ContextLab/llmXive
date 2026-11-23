"""Unit tests for the three data‑fetch loader functions.

Each loader is exercised by retrieving a single record (or file) and
asserting that the result is non‑empty. The tests rely on real network
access; failures indicate a problem with the loader implementation.
"""

import pathlib

import pytest

from code.utils.data_fetcher import (
    load_ms_marco,
    load_spider,
    load_dbpedia,
    DataFetchError,
)


def test_load_ms_marco():
    """Iterate a single record from the streamed MS MARCO test split."""
    try:
        ds = load_ms_marco()
    except DataFetchError as exc:
        pytest.fail(f"load_ms_marco raised DataFetchError: {exc}")

    # The streaming dataset is an iterable; fetch the first element.
    first = next(iter(ds), None)
    assert first is not None, "MS MARCO stream yielded no records"


def test_load_spider():
    """Iterate a single record from the streamed Spider tables split."""
    try:
        ds = load_spider()
    except DataFetchError as exc:
        pytest.fail(f"load_spider raised DataFetchError: {exc}")

    first = next(iter(ds), None)
    assert first is not None, "Spider stream yielded no records"


def test_load_dbpedia():
    """Download the DBpedia parquet file and verify its existence."""
    try:
        path = load_dbpedia()
    except DataFetchError as exc:
        pytest.fail(f"load_dbpedia raised DataFetchError: {exc}")

    assert isinstance(path, pathlib.Path), "load_dbpedia did not return a Path"
    assert path.is_file(), f"DBpedia file not found at {path}"
    assert path.stat().st_size > 0, "Downloaded DBpedia file is empty"