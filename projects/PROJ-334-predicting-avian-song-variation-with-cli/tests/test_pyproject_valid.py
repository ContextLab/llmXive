"""
Verify that pyproject.toml is syntactically valid TOML and contains the
required sections for the project metadata.
"""

import tomllib
from pathlib import Path

def test_pyproject_toml_valid():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert pyproject_path.is_file(), f"pyproject.toml not found at {pyproject_path}"

    # Load TOML using the standard library tomllib (Python 3.11+)
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    # Basic sanity checks
    assert isinstance(data, dict), "pyproject.toml did not parse to a dict."
    assert "project" in data, "[project] section missing in pyproject.toml."
    project_section = data["project"]
    assert isinstance(project_section, dict), "[project] should be a table."

    # Verify required keys
    required_keys = {"name", "version", "description", "requires-python"}
    missing = required_keys - project_section.keys()
    assert not missing, f"Missing required keys in [project] section: {missing}"