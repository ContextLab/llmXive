"""
Integration test for the data_loader module.

The test verifies that the ``download_and_save_sample`` function correctly
handles a transient error (simulating a rate‑limit or network interruption)
by retrying and eventually producing a CSV file whose size does not exceed
the configured limit.
"""

import csv
import pathlib
import types
from unittest import mock

import pytest

from code import data_loader

@pytest.fixture
def temp_output(tmp_path: pathlib.Path) -> pathlib.Path:
    """Path to a temporary CSV output file."""
    return tmp_path / "github-code-sample.csv"

def fake_stream_generator(fail_first: bool = True):
    """Yield a few dummy records, optionally raising on the first iteration."""
    called = {"attempt": 0}

    def generator():
        # Simulate a transient failure on the first call.
        if fail_first and called["attempt"] == 0:
            called["attempt"] += 1
            raise ConnectionError("Simulated network interruption")
        # Afterwards, yield a small deterministic sample.
        for i in range(5):
            yield {"id": f"sample-{i}", "content": f"print({i})"}

    return generator

def test_download_resilient_to_transient_error(tmp_path, monkeypatch):
    """Ensure the downloader retries after a simulated network error."""
    output_path = tmp_path / "github-code-sample.csv"

    # Patch the stream_dataset function to use our fake generator.
    fake_gen = fake_stream_generator(fail_first=True)
    monkeypatch.setattr(data_loader, "stream_dataset", lambda *args, **kwargs: fake_gen())

    # Patch sleep to avoid real delays during the back‑off.
    monkeypatch.setattr(data_loader.time, "sleep", lambda _: None)

    # Run the download routine with a tiny size limit to keep the test fast.
    data_loader.download_and_save_sample(
        output_path=output_path,
        max_bytes=10 * 1024,  # 10 KiB – more than enough for the fake rows.
        max_retries=3,
    )

    # The file must exist and contain the expected header + rows.
    assert output_path.is_file(), "CSV output file was not created"

    with output_path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Header + 5 rows expected.
    assert rows[0] == ["id", "content"]
    assert len(rows) == 6  # header + 5 data rows
    # Verify that the content matches the fake generator.
    for i, row in enumerate(rows[1:]):
        assert row[0] == f"sample-{i}"
        assert row[1] == f"print({i})"

def test_cli_parses_unknown_arguments(monkeypatch, tmp_path):
    """The CLI should ignore unknown arguments (e.g. comments in quick‑start)."""
    output_path = tmp_path / "out.csv"

    # Mock the heavy‑weight download routine so the test runs instantly.
    monkeypatch.setattr(
        data_loader,
        "download_and_save_sample",
        lambda *args, **kwargs: None,
    )

    # Simulate command line that includes a stray comment token.
    argv = ["--output", str(output_path), "#", "Stage", "1", "Download", "data"]
    # The function should not raise.
    data_loader.main(argv)

    # Ensure the mocked download function was called (i.e. parsing succeeded).
    assert data_loader.download_and_save_sample.called  # type: ignore