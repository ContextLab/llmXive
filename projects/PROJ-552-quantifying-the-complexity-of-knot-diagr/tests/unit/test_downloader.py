"""
Unit tests for the knot‑atlas downloader (T057).

The tests mock the ``database_knotinfo`` package to avoid network access.
They verify:
  * exponential back‑off timing,
  * creation of a partial cache after three consecutive simulated failures,
  * timeout handling.
"""

import json
import time
from pathlib import Path
from unittest import mock

import pytest

# The downloader implementation lives in ``code/download/knot_atlas_loader.py``.
from download.knot_atlas_loader import download_knot_atlas_data, save_raw_data

# Helper to create a temporary raw‑data file path.
@pytest.fixture
def raw_path(tmp_path: Path) -> Path:
    return tmp_path / "knot_atlas_raw.json"

# ----------------------------------------------------------------------
# Mock ``database_knotinfo`` to control the returned records.
# ----------------------------------------------------------------------


class MockKnotInfo:
    """Simple mock that mimics ``database_knotinfo.link_list``."""

    def __init__(self, records, fail_times=0, delay=0):
        self._records = records
        self._fail_times = fail_times
        self._delay = delay
        self._calls = 0

    def link_list(self):
        self._calls += 1
        if self._calls <= self._fail_times:
            raise RuntimeError("simulated download failure")
        time.sleep(self._delay)
        return self._records

# ----------------------------------------------------------------------
# Test exponential back‑off logic.
# ----------------------------------------------------------------------


def test_download_retry_logic(monkeypatch, raw_path: Path):
    """Verify that the downloader backs off 1 s → 2 s → 4 s on failures."""
    mock = MockKnotInfo(records=[{"name": "4_1"}], fail_times=2)

    # Patch the import inside the downloader.
    monkeypatch.setitem(
        sys.modules,
        "database_knotinfo",
        mock,
    )

    start = time.time()
    download_knot_atlas_data()
    elapsed = time.time() - start

    # Expected total back‑off delay = 1 + 2 = 3 s (the third attempt succeeds).
    assert 3 <= elapsed < 5, f"elapsed {elapsed:.2f}s not within expected range"

# ----------------------------------------------------------------------
# Test partial cache creation after three consecutive failures.
# ----------------------------------------------------------------------


def test_download_partial_cache(monkeypatch, tmp_path: Path):
    """After three failures a partial cache file should be written."""
    # Force three failures; the fourth call would succeed but we stop early.
    mock = MockKnotInfo(records=[{"name": "4_1"}], fail_times=3)
    monkeypatch.setitem(sys.modules, "database_knotinfo", mock)

    cache_path = tmp_path / "partial_cache.json"
    # The downloader looks for ``cache_path`` via a constant; we monkeypatch
    # the constant inside the module.
    import download.knot_atlas_loader as loader

    monkeypatch.setattr(loader, "PARTIAL_CACHE_PATH", cache_path)

    # Run the download – it should raise after exhausting retries.
    with pytest.raises(RuntimeError):
        download_knot_atlas_data()

    # The partial cache file must now exist and contain the (empty) result.
    assert cache_path.is_file()
    data = json.loads(cache_path.read_text())
    assert data == []  # empty list because no successful fetch occurred

# ----------------------------------------------------------------------
# Test timeout handling (simulated via a short ``time_limit`` argument).
# ----------------------------------------------------------------------


def test_download_timeout(monkeypatch):
    """A timeout shorter than the back‑off schedule should abort early."""
    mock = MockKnotInfo(records=[{"name": "4_1"}], fail_times=10, delay=0.5)
    monkeypatch.setitem(sys.modules, "database_knotinfo", mock)

    import download.knot_atlas_loader as loader

    # Set a very low timeout (1 s) – the downloader should abort before a
    # successful attempt.
    with pytest.raises(RuntimeError):
        loader.download_knot_atlas_data(time_limit=1)
