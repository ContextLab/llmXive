"""
test_user_composition.py

Unit tests for the ``validate_user_composition`` script (Task T003).

The tests cover three scenarios:
1. A CSV missing the required ``composition`` column – should raise ``ValueError``.
2. A CSV with an invalid composition object (empty dict) – should raise ``ValueError``.
3. A CSV with a valid composition – should pass without exception.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test.
from data.validate_user_composition import validate_user_composition


@pytest.fixture
def temp_dir():
    """Create and clean up a temporary directory for each test."""
    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        os.chdir(td)
        try:
            yield Path(td)
        finally:
            os.chdir(cwd)


def write_csv(path: Path, df: pd.DataFrame):
    """Utility to write a DataFrame to CSV in the temporary directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def test_missing_composition_column_raises(temp_dir):
    """CSV without a ``composition`` column should raise ValueError."""
    csv_path = temp_dir / "data" / "input" / "compositions.csv"
    df = pd.DataFrame({"not_composition": ["foo", "bar"]})
    write_csv(csv_path, df)

    with pytest.raises(ValueError) as excinfo:
        validate_user_composition(str(csv_path))

    assert "missing required field 'composition'" in str(excinfo.value)


def test_invalid_composition_object_raises(temp_dir):
    """Composition that does not satisfy the schema (e.g., empty dict) should raise."""
    csv_path = temp_dir / "data" / "input" / "compositions.csv"
    # Empty dict violates ``minProperties: 1`` in the schema.
    df = pd.DataFrame({"composition": ["{}"]})
    write_csv(csv_path, df)

    with pytest.raises(ValueError) as excinfo:
        validate_user_composition(str(csv_path))

    # The exact JSON‑schema message may vary; we check for a hint about the
    # composition object being invalid.
    assert "composition validation error" in str(excinfo.value)


def test_valid_composition_passes(temp_dir):
    """A correctly formatted composition should validate successfully."""
    csv_path = temp_dir / "data" / "input" / "compositions.csv"
    df = pd.DataFrame(
        {
            "composition": [
                '{"Fe":0.5,"Ni":0.5}',
                '{"Co":0.2,"Cr":0.2,"Fe":0.2,"Mn":0.2,"Ni":0.2}',
            ]
        }
    )
    write_csv(csv_path, df)

    # Should not raise any exception.
    result_df = validate_user_composition(str(csv_path))
    # Verify that the returned DataFrame matches the input.
    pd.testing.assert_frame_equal(
        result_df.reset_index(drop=True), df.reset_index(drop=True)
    )