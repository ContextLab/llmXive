"""
Unit tests for spec verification utilities.
"""
import pytest
from pathlib import Path
import tempfile
import os

from code.utils.spec_verifier import verify_wilcoxon_requirement, verify_gradcam_requirement


class TestSpecVerifier:
    """Tests for spec verification functions."""

    def test_verify_wilcoxon_requirement_found(self, tmp_path):
        """Test that verification passes when Wilcoxon requirement is present."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(
            "# Spec\n"
            "This spec requires a Wilcoxon signed-rank test for FR-005.\n"
        )
        assert verify_wilcoxon_requirement(spec_file) is True

    def test_verify_wilcoxon_requirement_not_found(self, tmp_path):
        """Test that verification fails when Wilcoxon requirement is absent."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(
            "# Spec\n"
            "This spec does not mention Wilcoxon tests.\n"
        )
        assert verify_wilcoxon_requirement(spec_file) is False

    def test_verify_gradcam_requirement_found(self, tmp_path):
        """Test that verification passes when Grad-CAM requirement is present."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(
            "# Spec\n"
            "This spec requires Grad-CAM heatmaps for FR-006.\n"
        )
        assert verify_gradcam_requirement(spec_file) is True

    def test_verify_gradcam_requirement_not_found(self, tmp_path):
        """Test that verification fails when Grad-CAM requirement is absent."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(
            "# Spec\n"
            "This spec does not mention Grad-CAM.\n"
        )
        assert verify_gradcam_requirement(spec_file) is False

    def test_verify_wilcoxon_file_not_found(self):
        """Test that FileNotFoundError is raised when spec is missing."""
        with pytest.raises(FileNotFoundError):
            verify_wilcoxon_requirement(Path("/nonexistent/spec.md"))

    def test_verify_gradcam_file_not_found(self):
        """Test that FileNotFoundError is raised when spec is missing."""
        with pytest.raises(FileNotFoundError):
            verify_gradcam_requirement(Path("/nonexistent/spec.md"))