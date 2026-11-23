"""
Unit test that verifies pipeline modules import and use the project logger.

The test imports a representative module (e.g., ``data_ingestion.download``),
runs a function that triggers a log entry, and then checks that the entry
appears in ``logs/pipeline.log``.
"""

import os
from pathlib import Path

import pytest

# Import a module that uses the logger; we choose the download script
from data_ingestion.download import parse_research_md_urls

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "pipeline.log"

def test_logger_writes_to_file(tmp_path, monkeypatch):
    """
    Ensure that calling a function that uses the logger creates an entry
    in ``logs/pipeline.log``.
    """
    # Ensure a clean log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    # Monkey‑patch the project root to a temporary directory containing a minimal
    # ``research.md`` so that ``parse_research_md_urls`` runs without error.
    minimal_md = tmp_path / "research.md"
    minimal_md.write_text(
        "# Data Sources\\n"
        "Example dataset: https://zenodo.org/record/1234567/files/example.tsv\\n"
    )
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

    # Run the function – it will log the discovered URL.
    urls = parse_research_md_urls()
    assert isinstance(urls, list) and len(urls) == 1

    # After the call, the logger should have written to the log file.
    assert LOG_FILE.exists(), "pipeline.log was not created"
    content = LOG_FILE.read_text()
    assert "Found URL:" in content or "Found URL:" in content  # at least one log entry
    # Clean up
    LOG_FILE.unlink()