"""
Unit test for the validation configuration generator.

The test ensures that ``generate_validation_config`` creates the expected
JSON file and that the ``top_n`` value matches the one defined in the
project's ``config.yaml``.
"""

import json
import os
from pathlib import Path

import pytest

# Import the function under test
from code.validate.generate_validation_config import generate_validation_config, main

# Import the config helper to obtain the expected default
from config import get_config

@pytest.fixture
def clean_output_path(tmp_path: Path) -> Path:
    """
    Provide a temporary output location for the JSON file and ensure a clean
    state before each test.
    """
    output = tmp_path / "validation_config.json"
    if output.exists():
        output.unlink()
    return output

def test_generate_validation_config_creates_file(clean_output_path: Path) -> None:
    """
    The generator must write a JSON file containing the correct ``top_n``.
    """
    # Run the generator with the temporary path
    result_path = generate_validation_config(output_path=clean_output_path)

    # Verify the function returned the correct path
    assert result_path == clean_output_path

    # The file must now exist
    assert result_path.is_file()

    # Load the JSON and compare with config.yaml
    with result_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    expected_top_n = get_config().get("top_n", 10)
    assert "top_n" in data
    assert data["top_n"] == expected_top_n

def test_main_writes_to_default_location(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """
    Running the module as a script should write to the default location.
    The test redirects the default location to a temporary directory to
    avoid polluting the repository.
    """
    default_path = Path("data/results/validation_config.json")
    temp_path = tmp_path / "validation_config.json"

    # Ensure the default path does not exist before the test
    if default_path.is_file():
        default_path.unlink()

    # Monkey‑patch Path.open to redirect writes to the temporary path
    original_open = Path.open

    def fake_open(self, *args, **kwargs):
        if self == default_path:
            return original_open(temp_path, *args, **kwargs)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)

    # Execute the script's main function
    main()

    # The temporary file should now exist with correct contents
    assert temp_path.is_file()
    with temp_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    expected_top_n = get_config().get("top_n", 10)
    assert data["top_n"] == expected_top_n