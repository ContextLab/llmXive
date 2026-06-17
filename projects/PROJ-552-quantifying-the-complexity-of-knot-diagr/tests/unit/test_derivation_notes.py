"""Unit test for the derivation notes generator.

The test ensures that the markdown file contains all four required
sections so that the ``DerivationNotesValidator`` will succeed.
"""

from pathlib import Path

import pytest

from reproducibility.generate_derivation_notes import generate_derivation_notes

@pytest.fixture
def notes_path(tmp_path: Path) -> Path:
    """Create a temporary notes file."""
    out = tmp_path / "derivation_notes.md"
    return generate_derivation_notes(out)

def test_derivation_notes_contains_all_sections(notes_path: Path):
    content = notes_path.read_text(encoding="utf-8")
    required_sections = [
        "Formula Citations with Page/Section References",
        "Step‑By‑Step Transformation Logic with Intermediate Values",
        "All Parameter Values Used",
        "Justification for Non‑Standard Choices",
    ]
    for section in required_sections:
        assert f"## {section}" in content, f"Missing section: {section}"