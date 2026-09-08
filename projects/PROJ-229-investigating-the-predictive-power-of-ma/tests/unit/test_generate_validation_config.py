"""
Unit test for the validation config generator.

This test ensures that the `generate_validation_config` function creates a
JSON file with the expected structure and respects the default value of
`top_n` when the configuration does not explicitly define it.
"""

import json
from pathlib import Path

import pytest

# Import the function from the artifact we just added.
from code.validate.generate_validation_config import generate_validation_config

@pytest.fixture
def temp_output(tmp_path: Path) -> Path:
    """Provide a temporary output path for the JSON file."""
    return tmp_path / "validation_config.json"

def test_generate_default_config(temp_output: Path):
    # Ensure no prior file exists.
    assert not temp_output.exists()

    # Call the generator; it will use the default top_n = 10.
    generate_validation_config(temp_output)

    # Verify the file was created.
    assert temp_output.is_file()

    # Load and inspect the JSON content.
    with temp_output.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "top_n" in data
    assert data["top_n"] == 10

def test_generate_custom_config(monkeypatch, temp_output: Path):
    # Patch the config loader to return a custom top_n.
    custom_cfg = {"top_n": 25}
    monkeypatch.setattr("config.get_config", lambda: custom_cfg)

    generate_validation_config(temp_output)

    with temp_output.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["top_n"] == 25