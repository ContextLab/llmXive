"""
Tests for the CI limits checker (code/ci_limits.py).

These tests verify that the script exits with the correct status code
depending on whether the provided monitoring CSV violates the RAM or
wall‑time limits.

The script's `main` function calls ``sys.exit``; in the tests we capture
the ``SystemExit`` exception and assert on its ``code`` attribute.
"""

import sys
import csv
import pathlib
import tempfile

# Import the main function from the ci_limits module.
from ci_limits import main, RAM_LIMIT_BYTES, TIME_LIMIT_SECONDS


def _write_csv(path: pathlib.Path, rows):
    """Utility to write a small CSV with the required columns."""
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["step", "wall_time_s", "peak_ram_bytes"])
        # Write data rows
        for row in rows:
            writer.writerow(row)


def test_ci_limits_compliant_csv(monkeypatch):
    """A CSV that respects both RAM and time limits should exit with code 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = pathlib.Path(tmpdir) / "monitoring_compliant.csv"
        # Create rows that sum to less than the time limit and have max RAM below the limit.
        rows = [
            ("step1", 1000, 1_000_000_000),  # 1 GB
            ("step2", 2000, 2_000_000_000),  # 2 GB
        ]
        _write_csv(csv_path, rows)

        # Monkey‑patch sys.argv so that ci_limits reads our file.
        monkeypatch.setattr(sys, "argv", ["ci_limits", str(csv_path)])

        # The script calls sys.exit; capture the SystemExit.
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0


def test_ci_limits_ram_violation(monkeypatch):
    """If any peak RAM exceeds the limit the script should exit with code 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = pathlib.Path(tmpdir) / "monitoring_ram_violation.csv"
        rows = [
            ("step1", 1000, RAM_LIMIT_BYTES + 1),  # Just over the RAM limit
            ("step2", 2000, 1_000_000_000),
        ]
        _write_csv(csv_path, rows)

        monkeypatch.setattr(sys, "argv", ["ci_limits", str(csv_path)])

        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1


def test_ci_limits_time_violation(monkeypatch):
    """If total wall‑time exceeds the limit the script should exit with code 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = pathlib.Path(tmpdir) / "monitoring_time_violation.csv"
        rows = [
            ("step1", TIME_LIMIT_SECONDS / 2, 1_000_000_000),
            ("step2", TIME_LIMIT_SECONDS / 2 + 1, 1_000_000_000),  # Sum > limit
        ]
        _write_csv(csv_path, rows)

        monkeypatch.setattr(sys, "argv", ["ci_limits", str(csv_path)])

        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1


def test_ci_limits_both_violations(monkeypatch):
    """When both RAM and time limits are violated the exit code is still 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = pathlib.Path(tmpdir) / "monitoring_both.csv"
        rows = [
            ("step1", TIME_LIMIT_SECONDS + 1, RAM_LIMIT_BYTES + 1),
        ]
        _write_csv(csv_path, rows)

        monkeypatch.setattr(sys, "argv", ["ci_limits", str(csv_path)])

        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1