import pathlib

import pytest


@pytest.fixture(scope="module")
def project_root() -> pathlib.Path:
    """
    Resolve the absolute path to the project root directory.
    The test file lives under ``tests/contract/``, so two parents up
    reaches the repository root.
    """
    return pathlib.Path(__file__).resolve().parents[2]


def test_readme_exists(project_root: pathlib.Path):
    """The top‑level README.md must be present."""
    readme_path = project_root / "README.md"
    assert readme_path.is_file(), "README.md not found at project root"


def test_readme_contains_required_sections(project_root: pathlib.Path):
    """
    Verify that the README includes the mandatory sections required for
    quick‑start documentation.
    """
    readme_path = project_root / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    required_sections = [
        "# llmXive Geometry Extension",
        "## Quick Start",
        "## Installation",
        "## Running Experiments",
    ]

    for section in required_sections:
        assert section in content, f"README.md missing required section: {section}"