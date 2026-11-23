"""
Traceability tests ensuring tasks are correctly linked to Functional Requirements.
"""
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
TRACEABILITY_DOC = PROJECT_ROOT / "docs" / "traceability.md"

class TestDirectoryTraceability:
    """Tests for T001d: Document traceability of directory-creation tasks."""

    def test_directory_traceability(self):
        """
        Assert that docs/traceability.md exists and documents the mapping
        between directory creation tasks (T001a, T001b) and Functional Requirements
        (FR-001, FR-002, FR-003).
        """
        assert TRACEABILITY_DOC.exists(), "Traceability document must exist."
        assert TRACEABILITY_DOC.stat().st_size > 0, "Traceability document must not be empty."

        content = TRACEABILITY_DOC.read_text()

        # Check for T001a references
        assert "T001a" in content, "T001a must be mentioned in traceability doc."
        assert "FR-001" in content, "FR-001 must be linked to T001a."
        assert "FR-002" in content, "FR-002 must be linked to T001a."

        # Check for T001b references
        assert "T001b" in content, "T001b must be mentioned in traceability doc."
        assert "FR-003" in content, "FR-003 must be linked to T001b."

        # Verify specific directory mentions to ensure content is specific, not generic
        assert "src/lib" in content or "src/metrics" in content, "Code directories should be referenced."
        assert "data/stimuli" in content or "data/processed" in content, "Data directories should be referenced."