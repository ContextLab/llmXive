"""
Unit tests for the reproducibility package creation and verification.
"""
import os
import sys
import tempfile
import zipfile
import shutil
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.create_reproducibility_package import create_reproducibility_package


class TestReproducibilityPackage:
    """Test suite for reproducibility package creation."""

    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary path for the output zip file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            yield tmp.name
        # Cleanup after test
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_package_creation(self, temp_output_path):
        """Test that the package is created successfully."""
        success = create_reproducibility_package(temp_output_path)
        assert success is True
        assert os.path.exists(temp_output_path)
        assert zipfile.is_zipfile(temp_output_path)

    def test_package_contains_required_files(self, temp_output_path):
        """Test that the package contains all required files."""
        create_reproducibility_package(temp_output_path)
        
        required_files = [
            "src/",
            "src/config/defaults.yaml",
            "scripts/run_full_suite.sh",
            "docs/README.md",
            "requirements.txt",
            "tests/"
        ]
        
        with zipfile.ZipFile(temp_output_path, 'r') as zipf:
            file_list = zipf.namelist()
            
            for required in required_files:
                # Check if the file or directory exists in the archive
                found = any(f.startswith(required) or f == required for f in file_list)
                assert found, f"Required file/directory {required} not found in package"

    def test_run_full_suite_script_is_executable(self, temp_output_path):
        """Test that run_full_suite.sh is included and has correct permissions."""
        create_reproducibility_package(temp_output_path)
        
        with zipfile.ZipFile(temp_output_path, 'r') as zipf:
            # Check if the script exists
            assert "scripts/run_full_suite.sh" in zipf.namelist()
            
            # Read the content to verify it's valid bash
            content = zipf.read("scripts/run_full_suite.sh").decode('utf-8')
            assert "#!/bin/bash" in content
            assert "run-full-sweep" in content

    def test_package_size_reasonable(self, temp_output_path):
        """Test that the package size is reasonable (not empty, not absurdly large)."""
        create_reproducibility_package(temp_output_path)
        
        size_bytes = os.path.getsize(temp_output_path)
        size_mb = size_bytes / (1024 * 1024)
        
        assert size_mb > 0.1, f"Package size {size_mb}MB is too small (likely empty)"
        assert size_mb < 500, f"Package size {size_mb}MB is too large (unexpected)"

    def test_package_can_be_extracted(self, temp_output_path):
        """Test that the package can be extracted successfully."""
        create_reproducibility_package(temp_output_path)
        
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(temp_output_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Verify some key files exist after extraction
            assert os.path.exists(os.path.join(extract_dir, "src"))
            assert os.path.exists(os.path.join(extract_dir, "scripts", "run_full_suite.sh"))
            assert os.path.exists(os.path.join(extract_dir, "docs", "README.md"))

    def test_script_content_valid(self, temp_output_path):
        """Test that run_full_suite.sh contains valid bash commands."""
        create_reproducibility_package(temp_output_path)
        
        with zipfile.ZipFile(temp_output_path, 'r') as zipf:
            content = zipf.read("scripts/run_full_suite.sh").decode('utf-8')
            
            # Check for essential components
            assert "set -e" in content or "set -euo pipefail" in content
            assert "python src/main.py" in content
            assert "run-full-sweep" in content
            assert "empirical_results.json" in content
            assert "statistical_report.json" in content
            assert "heavy_tailed_results.json" in content