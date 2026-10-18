"""
tests/spec_validation_test.py
------------------------------

Unit tests for ``code/spec_validation.py``.  The tests create temporary
specification files that deliberately contain or omit the required
phrases, invoke the verification functions and assert the expected
behaviour (success or ``RuntimeError`` with a log entry).
"""

import os
import shutil
from pathlib import Path

import pytest

# Import the functions under test
from code.spec_validation import (
    verify_sc001_valid_sites,
    verify_fr002_linear_slope_fallback,
)


@pytest.fixture
def temp_spec(tmp_path):
    """
    Create a temporary specification markdown file with the minimal
    structure required for the tests.
    """
    spec_dir = tmp_path / "specs" / "001-investigating-the-potential-benefits-of"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "spec.md"
    yield spec_path
    # Cleanup is automatic via tmp_path fixture


def write_content(spec_path: Path, include_sc: bool, include_fr: bool):
    """
    Helper to write a spec file containing the required phrases
    conditionally.
    """
    lines = ["# Project Specification", ""]
    if include_sc:
        lines.append("## SC-001")
        lines.append("The system must process up to 30 valid sites.")
    else:
        lines.append("## SC-001")
        lines.append("The system must process sites.")  # missing phrase

    if include_fr:
        lines.append("")
        lines.append("## FR-002")
        lines.append(
            "*Note: If non-linear asymptotic fitting fails (R² < 0.95), the linear slope fallback is the primary accepted metric for that site.*"
        )
    else:
        lines.append("")
        lines.append("## FR-002")
        lines.append("*Note: Non‑linear fitting fallback is used.*")  # missing phrase

    spec_path.write_text("\n".join(lines), encoding="utf-8")


def test_sc001_success(temp_spec):
    write_content(temp_spec, include_sc=True, include_fr=False)
    assert verify_sc001_valid_sites(spec_path=str(temp_spec)) is True


def test_sc001_failure(temp_spec):
    write_content(temp_spec, include_sc=False, include_fr=False)
    with pytest.raises(RuntimeError) as exc:
        verify_sc001_valid_sites(spec_path=str(temp_spec))
    assert "SC‑001 validation failed" in str(exc.value)
    # Verify that a log entry was written
    log_path = Path("logs") / "spec_validation.log"
    assert log_path.is_file()
    content = log_path.read_text(encoding="utf-8")
    assert "SC‑001 validation failed" in content
    # Clean up for next test
    shutil.rmtree(log_path.parent)


def test_fr002_success(temp_spec):
    write_content(temp_spec, include_sc=False, include_fr=True)
    assert verify_fr002_linear_slope_fallback(spec_path=str(temp_spec)) is True


def test_fr002_failure(temp_spec):
    write_content(temp_spec, include_sc=False, include_fr=False)
    with pytest.raises(RuntimeError) as exc:
        verify_fr002_linear_slope_fallback(spec_path=str(temp_spec))
    assert "FR‑002 validation failed" in str(exc.value)
    log_path = Path("logs") / "spec_validation.log"
    assert log_path.is_file()
    content = log_path.read_text(encoding="utf-8")
    assert "FR‑002 validation failed" in content
    # Clean up
    shutil.rmtree(log_path.parent)
