"""Test that the citation‑validation script produces the expected JSON.

The test runs the ``code.validate_citations`` module and asserts that the
output file exists and that every entry contains a ``status`` field set to
``"verified"``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

def test_citation_validation_report():
    # Execute the script via its entry point.
    from code.validate_citations import main as validate_main

    rc = validate_main([])
    assert rc == 0, "Citation validation script exited with non‑zero code"

    report_path = paths.reports("citation_validation.json")
    assert report_path.is_file(), f"Report not found at {report_path}"

    with report_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # The report should be a list of dicts.
    assert isinstance(data, list), "Report JSON is not a list"
    assert data, "Report JSON is empty"

    for entry in data:
        assert isinstance(entry, dict), "Report entry is not a dict"
        assert entry.get("status") == "verified", (
            f"Citation status not verified for entry: {entry}"
        )
        assert "citation" in entry, "Missing 'citation' field"
        assert "source" in entry, "Missing 'source' field"