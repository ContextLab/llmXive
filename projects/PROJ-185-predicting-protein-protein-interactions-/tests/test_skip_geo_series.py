import os
import json
from pathlib import Path

import pytest

from src.pipeline.download import process_series, build_parser


@pytest.fixture
def clean_log():
    """
    Ensure that the pipeline log file does not exist before each test and is removed afterwards.
    """
    log_path = "pipeline.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    yield
    if os.path.exists(log_path):
        os.remove(log_path)


@pytest.fixture
def clean_state():
    """
    Remove the artifact hash state file before and after each test to guarantee a clean environment.
    """
    state_path = "state/artifact_hashes.yaml"
    if os.path.exists(state_path):
        os.remove(state_path)
    yield
    if os.path.exists(state_path):
        os.remove(state_path)


def _make_args(tmp_path: Path, series_id: str):
    """
    Helper to construct a minimal argparse.Namespace that mimics the arguments
    produced by the CLI parser for the downloader.
    """
    parser = build_parser()
    # Parse an empty list to get defaults, then override the fields we need.
    args = parser.parse_args([])
    args.series = series_id
    args.output_dir = str(tmp_path)
    # The downloader may look for these flags; set sensible defaults.
    args.force = False
    args.verbose = False
    return args


def test_skip_series_with_few_samples(tmp_path, clean_log, clean_state, monkeypatch):
    """
    Verify that a GEO series with fewer than the required 30 samples is skipped.
    The function should return ``None`` and emit a warning in ``pipeline.log``.
    """
    series_id = "GSE_SMALL"
    args = _make_args(tmp_path, series_id)

    # Monkey‑patch the internal helper that determines the sample count.
    # The actual implementation name is ``_get_sample_count`` – this matches the
    # name introduced in task T043.
    def fake_get_sample_count(sid):
        assert sid == series_id
        return 10  # fewer than the 30‑sample threshold

    import src.pipeline.download as dl
    monkeypatch.setattr(dl, "_get_sample_count", fake_get_sample_count)

    # Run the downloader; it should recognise the low sample count and skip.
    result = process_series(series_id, args)
    assert result is None, "process_series should return None when skipping a series"

    # The warning must be recorded in the pipeline log.
    with open("pipeline.log") as log_file:
        log_contents = log_file.read()
    assert f"Skipping GEO series {series_id}" in log_contents, "Expected skip warning not found in log"


def test_process_series_with_enough_samples(tmp_path, clean_log, clean_state, monkeypatch):
    """
    Verify that a GEO series with a sufficient number of samples is processed normally.
    The function should not emit a skip warning and should return a non‑None value.
    """
    series_id = "GSE_LARGE"
    args = _make_args(tmp_path, series_id)

    # Monkey‑patch the sample‑count helper to report a sufficient number.
    def fake_get_sample_count(sid):
        assert sid == series_id
        return 50  # meets the minimum requirement

    import src.pipeline.download as dl
    monkeypatch.setattr(dl, "_get_sample_count", fake_get_sample_count)

    # Monkey‑patch the actual download routine to avoid network I/O.
    def fake_download_series(sid, out_dir):
        """
        Simulate a successful download by creating a dummy file.
        """
        os.makedirs(out_dir, exist_ok=True)
        dummy_path = Path(out_dir) / f"{sid}_data.txt"
        dummy_path.write_text("dummy content")
        return True

    monkeypatch.setattr(dl, "_download_series", fake_download_series)

    # Run the downloader; it should proceed without skipping.
    result = process_series(series_id, args)
    assert result is not None, "process_series should return a truthy value for a valid series"

    # Ensure no skip warning was logged.
    with open("pipeline.log") as log_file:
        log_contents = log_file.read()
    assert f"Skipping GEO series {series_id}" not in log_contents, "Unexpected skip warning for a valid series"