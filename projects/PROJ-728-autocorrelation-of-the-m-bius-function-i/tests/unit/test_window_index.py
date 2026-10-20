"""
Unit test for the deterministic window index generator (T004).

The test runs the ``code.window_index`` script, checks that the output
CSV exists, contains exactly 300 rows (100 windows for each of the three
interval lengths), and verifies that windows belonging to the same
interval length do not overlap.
"""

import csv
from pathlib import Path

import pytest

# Import the generation function directly to avoid subprocess overhead.
from code.window_index import generate_window_index, DEFAULT_OUTPUT


@pytest.fixture(scope="module")
def csv_path(tmp_path_factory):
    """Generate the CSV in a temporary directory for isolation."""
    out_path = tmp_path_factory.getbasetemp() / "window_index.csv"
    generate_window_index(
        N=10_000_000,
        L_values=[1000, 10_000, 100_000],
        windows_per_L=100,
        seed=20231017,
        output_path=out_path,
    )
    return out_path


def test_csv_exists(csv_path: Path):
    assert csv_path.is_file(), f"CSV file not found at {csv_path}"


def test_row_count(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Header + 300 data rows
    assert len(rows) == 301, f"Expected 301 lines (header + 300 rows), got {len(rows)}"


def test_non_overlapping_windows(csv_path: Path):
    """
    Verify that windows for the same interval length do not overlap.
    """
    windows_by_L = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = int(row["interval_start"])
            L = int(row["interval_length"])
            windows_by_L.setdefault(L, []).append(start)

    for L, starts in windows_by_L.items():
        # Sort starts to simplify overlap check
        starts_sorted = sorted(starts)
        for i in range(1, len(starts_sorted)):
            prev_start = starts_sorted[i - 1]
            cur_start = starts_sorted[i]
            assert cur_start >= prev_start + L, (
                f"Overlap detected for L={L}: window starting at {prev_start} "
                f"overlaps with window starting at {cur_start}"
            )