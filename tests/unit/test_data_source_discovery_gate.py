"""Unit tests for the PURE verification gate (no network, no LLM, no venv).

These cover only ``parse_records_gate`` — the load-bearing decision that filters
out LLM hallucinations: a recipe that prints ``RECORDS=0`` or that raises
(non-zero exit, e.g. ImportError) is REJECTED; one that prints a non-zero
``RECORDS=<n>`` is accepted. The optional ``FIELDS=...`` line populates
``sample_fields``.
"""
from __future__ import annotations

from llmxive.librarian.data_source_discovery import parse_records_gate


def test_accepts_nonzero_records() -> None:
    gate = parse_records_gate(0, "loaded data\nRECORDS=250\n", "")
    assert gate.verified is True
    assert gate.record_count == 250
    assert gate.sample_fields == []


def test_rejects_zero_records() -> None:
    gate = parse_records_gate(0, "RECORDS=0\n", "")
    assert gate.verified is False
    assert gate.record_count == 0
    assert gate.reason is not None


def test_rejects_nonzero_exit_importerror() -> None:
    # An ImportError-style failure: non-zero exit, traceback on stderr.
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "<string>", line 1, in <module>\n'
        "ModuleNotFoundError: No module named 'knotinfo'\n"
    )
    gate = parse_records_gate(1, "", stderr)
    assert gate.verified is False
    assert "ModuleNotFoundError" in (gate.reason or "")


def test_rejects_missing_marker() -> None:
    gate = parse_records_gate(0, "it ran but printed nothing useful\n", "")
    assert gate.verified is False
    assert gate.reason is not None


def test_parses_fields_line() -> None:
    stdout = "RECORDS=12967\nFIELDS=name, crossing_number, braid_index, volume\n"
    gate = parse_records_gate(0, stdout, "")
    assert gate.verified is True
    assert gate.record_count == 12967
    assert gate.sample_fields == [
        "name",
        "crossing_number",
        "braid_index",
        "volume",
    ]
