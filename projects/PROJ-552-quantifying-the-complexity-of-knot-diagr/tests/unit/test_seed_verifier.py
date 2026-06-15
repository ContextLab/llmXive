"""
Unit tests for seed_verifier module.
Tests seed verification functionality per T058 requirements.
"""
import pytest
from pathlib import Path
import tempfile
import os

from reproducibility.seed_verifier import (
    SeedVerifier,
    RandomOperation,
    SeedVerificationResult
)


class TestSeedVerifier:
    """Test cases for SeedVerifier class."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        # Create code directory
        code_dir = tmp_path / 'code'
        code_dir.mkdir()

        # Create a test Python file with seed pinning
        test_file = code_dir / 'test_module.py'
        test_file.write_text("""
import numpy as np
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_data():
    return np.random.randn(100)
""")

        return tmp_path

    @pytest.fixture
    def temp_project_no_seed(self, tmp_path):
        """Create a temporary project without seed pinning."""
        code_dir = tmp_path / 'code'
        code_dir.mkdir()

        test_file = code_dir / 'test_module.py'
        test_file.write_text("""
import numpy as np
import random

def generate_data():
    return np.random.randn(100)
""")

        return tmp_path

    def test_find_python_files(self, temp_project):
        """Test finding Python files in code/ directory."""
        verifier = SeedVerifier(temp_project)
        files = verifier.find_python_files()

        assert len(files) == 1
        assert files[0].name == 'test_module.py'

    def test_scan_file_with_seed(self, temp_project):
        """Test scanning a file with seed pinning."""
        verifier = SeedVerifier(temp_project)
        files = verifier.find_python_files()

        for f in files:
            operations = verifier.scan_file_for_random_ops(f)
            assert len(operations) > 0

            # Check that seed pinning is detected
            for op in operations:
                if 'random' in op.operation_type:
                    assert op.has_seed_pin is True

    def test_scan_file_without_seed(self, temp_project_no_seed):
        """Test scanning a file without seed pinning."""
        verifier = SeedVerifier(temp_project_no_seed)
        files = verifier.find_python_files()

        for f in files:
            operations = verifier.scan_file_for_random_ops(f)
            assert len(operations) > 0

            # Check that seed pinning is NOT detected
            for op in operations:
                if 'random' in op.operation_type:
                    assert op.has_seed_pin is False

    def test_verify_file_compliant(self, temp_project):
        """Test verifying a compliant file."""
        verifier = SeedVerifier(temp_project)
        files = verifier.find_python_files()

        for f in files:
            result = verifier.verify_file(f)
            assert result.is_compliant is True
            assert result.unpinned_ops == 0

    def test_verify_file_non_compliant(self, temp_project_no_seed):
        """Test verifying a non-compliant file."""
        verifier = SeedVerifier(temp_project_no_seed)
        files = verifier.find_python_files()

        for f in files:
            result = verifier.verify_file(f)
            assert result.is_compliant is False
            assert result.unpinned_ops > 0

    def test_generate_report(self, temp_project):
        """Test report generation."""
        verifier = SeedVerifier(temp_project)
        results = verifier.verify_all()

        report = verifier.generate_report(results)

        assert '# Seed Verification Report' in report
        assert 'Compliance Status' in report
        assert 'File-by-File Breakdown' in report
        assert 'Pinned Seed Values' in report

    def test_extract_seed_value(self, temp_project):
        """Test seed value extraction."""
        verifier = SeedVerifier(temp_project)
        content = (temp_project / 'code' / 'test_module.py').read_text()

        seed_value = verifier._extract_seed_value(content)
        assert seed_value == 42

if __name__ == '__main__':
    pytest.main([__file__, '-v'])