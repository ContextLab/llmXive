"""
tests/test_validate.py
-----------------------

Unit tests for the validation script (T004).

The tests cover:
* Correct handling of the <50‑row error.
* Proper logging of the row count and the power‑target warning.
* Generation of the SHA‑256 checksum file.
"""

import os
import re
from pathlib import Path

import pandas as pd
import pytest

from src.data.validate import main as validate_main
from llmxive_toolkit import paths

@pytest.fixture
def features_path(tmp_path: Path) -> Path:
    """Create a temporary ``features.csv`` file."""
    # Default location used by ``src.data.validate``.
    target = paths.data("processed", "features.csv")
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write a minimal CSV with the required columns (descriptor columns are not
    # needed for the validation step itself).
    df = pd.DataFrame(
        {
            "composition": ["BaTiO3", "SrTiO3"],
            "formation_energy": [1.2, 0.9],
            "A_atomic_radius": [1.35, 1.35],
            "B_atomic_radius": [0.86, 0.86],
            "X_atomic_radius": [0.66, 0.66],
            "A_electronegativity": [0.9, 0.9],
            "B_electronegativity": [1.5, 1.5],
            "X_electronegativity": [3.0, 3.0],
            "A_oxidation_state": [2, 2],
            "B_oxidation_state": [4, 4],
            "X_oxidation_state": [-2, -2],
            "A_valence_electrons": [2, 2],
            "B_valence_electrons": [5, 5],
            "X_valence_electrons": [6, 6],
        }
    )
    df.to_csv(target, index=False)
    return target

def test_validation_success(tmp_path: Path, features_path: Path):
    """
    With a row count between 50 and 500 the script should write the log
    (containing the row count) and the checksum file, without raising.
    """
    # Ensure we have at least 50 rows but fewer than 500.
    df = pd.read_csv(features_path)
    # Duplicate rows to reach 60 rows.
    df = pd.concat([df] * 30, ignore_index=True)
    df.to_csv(features_path, index=False)

    # Run validation.
    validate_main()

    # Check log content.
    log_path = paths.data("processed", "validation.log")
    assert log_path.is_file()
    content = log_path.read_text()
    assert re.search(r"Total rows in feature matrix: 60", content)
    # Because 60 < 500 we expect the warning line.
    assert "Warning: power target (>= 500 rows) not met" in content

    # Check checksum file.
    checksum_path = paths.data("checksums", "validation.sha256")
    assert checksum_path.is_file()
    checksum = checksum_path.read_text().strip()
    assert re.fullmatch(r"[0-9a-fA-F]{64}", checksum)

def test_validation_insufficient_rows():
    """
    When the feature matrix has fewer than 50 rows the script must raise
    ``ValueError`` with the exact required message.
    """
    # Create a tiny CSV (10 rows).
    df = pd.DataFrame(
        {
            "composition": ["BaTiO3"] * 10,
            "formation_energy": [1.0] * 10,
            "A_atomic_radius": [1.0] * 10,
            "B_atomic_radius": [1.0] * 10,
            "X_atomic_radius": [1.0] * 10,
            "A_electronegativity": [1.0] * 10,
            "B_electronegativity": [1.0] * 10,
            "X_electronegativity": [1.0] * 10,
            "A_oxidation_state": [1] * 10,
            "B_oxidation_state": [1] * 10,
            "X_oxidation_state": [-2] * 10,
            "A_valence_electrons": [1] * 10,
            "B_valence_electrons": [1] * 10,
            "X_valence_electrons": [6] * 10,
        }
    )
    small_path = paths.data("processed", "features.csv")
    small_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(small_path, index=False)

    with pytest.raises(ValueError) as excinfo:
        validate_main()
    assert str(excinfo.value) == "Insufficient rows (<50) for 5-fold CV"