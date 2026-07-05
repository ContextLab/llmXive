"""
Tests for the validators.py module.

These tests verify that the "Real Data Only" constraint is properly enforced,
rejecting synthetic or placeholder data while allowing real data.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from validators import (
    RealDataValidationError,
    check_file_for_synthetic_content,
    validate_raw_directory,
    enforce_real_data_constraint,
    validate_accession_data,
    SYNTHETIC_SIGNATURES,
    PLACEHOLDER_FILE_PATTERNS,
    MIN_REAL_FILE_SIZE
)


class TestCheckFileForSyntheticContent:
    """Tests for the check_file_for_synthetic_content function."""

    def test_real_csv_file(self, tmp_path):
        """Test that a real-looking CSV file passes validation."""
        # Create a real-looking count matrix
        csv_content = """Gene,Cell1,Cell2,Cell3
        Gene1,10,5,12
        Gene2,0,8,3
        Gene3,15,2,9
        Gene4,7,11,4
        Gene5,3,6,14"""

        file_path = tmp_path / "GSE12345_counts.csv"
        file_path.write_text(csv_content)

        is_synthetic, patterns = check_file_for_synthetic_content(file_path)

        assert not is_synthetic, "Real CSV file should not be flagged as synthetic"
        assert len(patterns) == 0, f"No patterns should be detected, got: {patterns}"

    def test_synthetic_signature_in_content(self, tmp_path):
        """Test that files containing synthetic signatures are detected."""
        csv_content = """Gene,Cell1,Cell2
        Gene1,10,5
        # This is synthetic data for testing
        Gene2,0,8"""

        file_path = tmp_path / "test_data.csv"
        file_path.write_text(csv_content)

        is_synthetic, patterns = check_file_for_synthetic_content(file_path)

        assert is_synthetic, "File with 'synthetic' signature should be detected"
        assert any("synthetic" in p for p in patterns), f"Should detect synthetic pattern: {patterns}"

    def test_placeholder_filename(self, tmp_path):
        """Test that files with placeholder in filename are detected."""
        # Create a file with placeholder in name
        file_path = tmp_path / "synthetic_counts.csv"
        file_path.write_text("Gene,Cell1\nGene1,10\n")

        is_synthetic, patterns = check_file_for_synthetic_content(file_path)

        assert is_synthetic, "File with 'synthetic' in name should be detected"
        assert any("filename_contains_synthetic" in p for p in patterns), f"Should detect filename pattern: {patterns}"

    def test_small_file(self, tmp_path):
        """Test that very small files are flagged."""
        file_path = tmp_path / "small_data.csv"
        file_path.write_text("a,b\n1,2\n")  # Very small file

        is_synthetic, patterns = check_file_for_synthetic_content(file_path)

        # Small files should be flagged
        assert "file_too_small" in patterns, f"Small file should be flagged: {patterns}"

    def test_sequential_naming_pattern(self, tmp_path):
        """Test detection of sequential naming patterns in synthetic data."""
        csv_content = """Gene,Cell1,Cell2
        gene1,10,5
        gene2,0,8
        gene3,15,2"""

        file_path = tmp_path / "data.csv"
        file_path.write_text(csv_content)

        is_synthetic, patterns = check_file_for_synthetic_content(file_path)

        # This might be flagged due to sequential naming
        # The test is flexible as this detection is heuristic
        if is_synthetic:
            assert any("sequential" in p for p in patterns), f"Should detect sequential pattern: {patterns}"


class TestValidateRawDirectory:
    """Tests for the validate_raw_directory function."""

    def test_empty_directory(self, tmp_path):
        """Test validation of an empty directory."""
        is_valid, violations = validate_raw_directory(tmp_path)

        assert is_valid, "Empty directory should pass validation"
        assert len(violations) == 0, "No violations should be reported for empty directory"

    def test_directory_with_real_files(self, tmp_path):
        """Test validation of a directory with real files."""
        # Create real-looking files
        for accession in ["GSE12345", "GSE67890"]:
            csv_content = f"""Gene,Cell1,Cell2,Cell3
        Gene1,10,5,12
        Gene2,0,8,3
        Gene3,15,2,9"""
            file_path = tmp_path / f"{accession}_counts.csv"
            file_path.write_text(csv_content)

        is_valid, violations = validate_raw_directory(tmp_path)

        assert is_valid, "Directory with real files should pass validation"
        assert len(violations) == 0, "No violations should be reported for real files"

    def test_directory_with_synthetic_files(self, tmp_path):
        """Test validation of a directory with synthetic files."""
        # Create a synthetic file
        file_path = tmp_path / "synthetic_data.csv"
        file_path.write_text("""Gene,Cell1
        Gene1,10
        # Synthetic data""")

        is_valid, violations = validate_raw_directory(tmp_path)

        assert not is_valid, "Directory with synthetic files should fail validation"
        assert len(violations) == 1, f"Should have 1 violation, got: {len(violations)}"
        assert "synthetic_data.csv" in violations[0]['file'], "Violation should reference the synthetic file"

    def test_directory_with_mixed_files(self, tmp_path):
        """Test validation of a directory with both real and synthetic files."""
        # Create a real file
        real_file = tmp_path / "GSE12345_counts.csv"
        real_file.write_text("""Gene,Cell1,Cell2
        Gene1,10,5
        Gene2,0,8""")

        # Create a synthetic file
        synthetic_file = tmp_path / "mock_data.csv"
        synthetic_file.write_text("""Gene,Cell1
        Gene1,10
        # Mock data""")

        is_valid, violations = validate_raw_directory(tmp_path)

        assert not is_valid, "Directory with mixed files should fail validation"
        assert len(violations) == 1, f"Should have 1 violation for synthetic file, got: {len(violations)}"
        assert "mock_data.csv" in violations[0]['file'], "Violation should reference the synthetic file"


class TestEnforceRealDataConstraint:
    """Tests for the enforce_real_data_constraint function."""

    def test_valid_directory(self, tmp_path):
        """Test that a valid directory passes enforcement."""
        # Create real-looking files
        file_path = tmp_path / "GSE12345_counts.csv"
        file_path.write_text("""Gene,Cell1,Cell2
        Gene1,10,5
        Gene2,0,8""")

        # This should not raise an exception
        result = enforce_real_data_constraint(tmp_path)

        assert result is True, "Valid directory should pass enforcement"

    def test_invalid_directory(self, tmp_path):
        """Test that an invalid directory raises an exception."""
        # Create a synthetic file
        file_path = tmp_path / "synthetic_data.csv"
        file_path.write_text("""Gene,Cell1
        Gene1,10
        # Synthetic data""")

        # This should raise RealDataValidationError
        with pytest.raises(RealDataValidationError) as exc_info:
            enforce_real_data_constraint(tmp_path)

        assert "Real data validation failed" in str(exc_info.value), "Should raise RealDataValidationError"

    def test_nonexistent_directory(self, tmp_path):
        """Test that a nonexistent directory passes enforcement (no files to validate)."""
        nonexistent_dir = tmp_path / "nonexistent"

        # This should not raise an exception
        result = enforce_real_data_constraint(nonexistent_dir)

        assert result is True, "Nonexistent directory should pass enforcement (no files)"


class TestValidateAccessionData:
    """Tests for the validate_accession_data function."""

    def test_valid_accession(self, tmp_path):
        """Test validation of a valid accession."""
        # Create a real file for the accession
        file_path = tmp_path / "GSE12345_counts.csv"
        file_path.write_text("""Gene,Cell1,Cell2
        Gene1,10,5
        Gene2,0,8""")

        # This should not raise an exception
        result = validate_accession_data("GSE12345", tmp_path)

        assert result is True, "Valid accession should pass validation"

    def test_invalid_accession(self, tmp_path):
        """Test validation of an accession with synthetic data."""
        # Create a synthetic file for the accession
        file_path = tmp_path / "GSE12345_synthetic.csv"
        file_path.write_text("""Gene,Cell1
        Gene1,10
        # Synthetic data""")

        # This should raise RealDataValidationError
        with pytest.raises(RealDataValidationError) as exc_info:
            validate_accession_data("GSE12345", tmp_path)

        assert "Real data validation failed" in str(exc_info.value), "Should raise RealDataValidationError"

    def test_no_files_for_accession(self, tmp_path):
        """Test validation when no files exist for an accession."""
        # This should not raise an exception (no files to validate)
        result = validate_accession_data("GSE99999", tmp_path)

        assert result is True, "Missing accession should pass validation (no files)"


class TestRealDataValidationIntegration:
    """Integration tests for real data validation."""

    def test_full_pipeline_validation(self, tmp_path):
        """Test the full validation workflow with mixed data."""
        # Create a realistic directory structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create real files
        for accession in ["GSE131907", "GSE111322"]:
            csv_content = f"""Gene,Cell1,Cell2,Cell3,Cell4,Cell5
        Gene1,10,5,12,8,15
        Gene2,0,8,3,11,2
        Gene3,15,2,9,6,14
        Gene4,7,11,4,9,5
        Gene5,3,6,14,7,10"""
            file_path = raw_dir / f"{accession}_counts.csv"
            file_path.write_text(csv_content)

        # Create a synthetic file
        synthetic_file = raw_dir / "GSE150728_placeholder.csv"
        synthetic_file.write_text("""Gene,Cell1
        Gene1,10
        # Placeholder data""")

        # Validate the directory
        is_valid, violations = validate_raw_directory(raw_dir)

        assert not is_valid, "Directory with synthetic file should fail validation"
        assert len(violations) == 1, f"Should have 1 violation, got: {len(violations)}"
        assert "GSE150728_placeholder.csv" in violations[0]['file'], "Should detect the synthetic file"

        # Verify the violation details
        violation = violations[0]
        assert violation['status'] == 'REJECTED', "Violation status should be REJECTED"
        assert len(violation['detected_patterns']) > 0, "Should have detected patterns"