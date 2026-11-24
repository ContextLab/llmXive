"""
tests/test_normalize_data.py
---------------------------

Unit tests for ``code/normalize_data.py`` (Task T004c-normalize).

The tests create a temporary ``data/raw`` directory, populate it with a
mixture of CSV files, invoke the ``normalize_dataset`` function, and verify
that the canonical file ``barrier_dataset.csv`` is produced with the
expected contents.
"""

import shutil
from pathlib import Path

import pytest

# Import the functions directly from the module under test
from normalize_data import (
    find_csv_candidates,
    select_target_csv,
    normalize_dataset,
)


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    """
    Provide a fresh ``data/raw`` directory for each test.
    """
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    return raw


def create_csv(path: Path, size: int, content: str = "col1,col2\n") -> None:
    """
    Helper that creates a CSV file of approximately *size* bytes.
    """
    # Write the header first
    path.write_text(content, encoding="utf-8")
    # Pad the file to reach the desired size (if possible)
    current = path.stat().st_size
    if size > current:
        padding = "a" * (size - current)
        with path.open("a", encoding="utf-8") as f:
            f.write(padding)


def test_selects_barrier_pattern_when_present(raw_dir: Path):
    # Create a non‑matching CSV (small)
    create_csv(raw_dir / "small.csv", size=100)
    # Create a matching CSV (larger)
    create_csv(raw_dir / "my_barrier_data.csv", size=500)

    candidates = find_csv_candidates(raw_dir, get_logger(__name__))
    selected = select_target_csv(candidates, get_logger(__name__))

    assert selected.name == "my_barrier_data.csv"
    # The selected file should be moved to the canonical name
    canonical = normalize_dataset(raw_dir, get_logger(__name__))
    assert canonical == raw_dir / "barrier_dataset.csv"
    assert canonical.read_text().startswith("col1,col2")


def test_falls_back_to_largest_csv_when_no_pattern(raw_dir: Path):
    # Two CSV files, none contain the word “barrier”
    create_csv(raw_dir / "a.csv", size=200)
    create_csv(raw_dir / "b.csv", size=400)

    candidates = find_csv_candidates(raw_dir, get_logger(__name__))
    selected = select_target_csv(candidates, get_logger(__name__))

    assert selected.name == "b.csv"

    # Normalization should rename the largest file
    canonical = normalize_dataset(raw_dir, get_logger(__name__))
    assert canonical == raw_dir / "barrier_dataset.csv"
    assert canonical.read_text().startswith("col1,col2")


def test_raises_when_no_csv_found(raw_dir: Path):
    # No CSV files at all
    with pytest.raises(FileNotFoundError):
        normalize_dataset(raw_dir, get_logger(__name__))