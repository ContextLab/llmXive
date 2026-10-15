"""
Tests for ``code/ingestion/flag_source.py``.

The tests create a temporary project‑root‑like directory, monkey‑patch
``utils.config.get_project_root`` to point to it, and verify that the
generated ``data_source_flag.json`` contains the expected ``source`` value.
"""

import json
from pathlib import Path
import pytest

# Import the module under test
from ingestion.flag_source import main as flag_source_main, _determine_source


@pytest.fixture
def temp_project_root(tmp_path, monkeypatch):
    """
    Prepare a temporary project root with the expected directory layout.
    """
    # Create required directories
    (tmp_path / "data" / "raw").mkdir(parents=True)
    # Monkey‑patch the config helper to return our temporary root
    monkeypatch.setattr("utils.config.get_project_root", lambda: tmp_path)
    return tmp_path


def write_dataset(root: Path):
    """Create an empty ``dataset.csv`` file."""
    dataset_path = root / "data" / "raw" / "dataset.csv"
    dataset_path.touch()
    return dataset_path


def test_flag_source_real(temp_project_root):
    """
    When ``plan.md`` contains a non‑empty ``Dataset URL:``, the flag must be
    ``real``.
    """
    # Arrange
    plan_path = temp_project_root / "plan.md"
    plan_path.write_text("Dataset URL: https://example.com/fake.csv\n")
    write_dataset(temp_project_root)

    # Act
    flag_source_main()

    # Assert
    flag_path = temp_project_root / "data" / "data_source_flag.json"
    assert flag_path.is_file()
    content = json.loads(flag_path.read_text())
    assert content["source"] == "real"


def test_flag_source_synthetic_without_url(temp_project_root):
    """
    If ``plan.md`` does not contain a URL, the source must be ``synthetic``.
    """
    # Arrange
    (temp_project_root / "plan.md").write_text("Some other content\n")
    write_dataset(temp_project_root)

    # Act
    flag_source_main()

    # Assert
    flag_path = temp_project_root / "data" / "data_source_flag.json"
    assert flag_path.is_file()
    content = json.loads(flag_path.read_text())
    assert content["source"] == "synthetic"


def test_flag_source_missing_dataset_raises(temp_project_root):
    """
    The helper should raise ``FileNotFoundError`` when the dataset file is
    absent.
    """
    # No dataset.csv created
    plan_path = temp_project_root / "plan.md"
    plan_path.write_text("Dataset URL: https://example.com/fake.csv\n")

    with pytest.raises(FileNotFoundError):
        _determine_source(temp_project_root)