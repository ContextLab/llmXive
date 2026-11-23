"""
Tests for the reproducibility package generation (T031).

Verifies that:
1. The package is created successfully
2. Required files are included
3. Sensitive files are excluded
4. Package is a valid tar.gz archive
"""

import unittest
import os
import sys
import tarfile
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.generate_reproducibility_package import (
    should_exclude,
    create_reproducibility_package,
    EXCLUDE_PATTERNS,
    INCLUDE_DIRS,
    INCLUDE_FILES,
)


class TestReproducibilityPackage(unittest.TestCase):
    """Test cases for reproducibility package generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create required directory structure
        (self.project_root / "data" / "analysis_results").mkdir(parents=True)
        (self.project_root / "data" / "interaction_logs").mkdir(parents=True)
        (self.project_root / "code" / "analysis").mkdir(parents=True)
        (self.project_root / "code" / "data_prep").mkdir(parents=True)
        (self.project_root / "code" / "utils").mkdir(parents=True)
        (self.project_root / "contracts").mkdir(parents=True)
        (self.project_root / "specs").mkdir(parents=True)

        # Create required files
        (self.project_root / "data" / "analysis_results" / "results.csv").write_text("metric,value\naccuracy,0.95")
        (self.project_root / "data" / "interaction_logs" / "anonymized_logs.csv").write_text("participant_id,task_id\nP1,T1")
        (self.project_root / "README.md").write_text("# Test README")
        (self.project_root / "requirements.txt").write_text("pandas\nnumpy")
        (self.project_root / ".env.example").write_text("TEST_VAR=value")

        # Create a sensitive file that should be excluded
        (self.project_root / "data" / "consent").mkdir(parents=True)
        (self.project_root / "data" / "consent" / "consent_form.pdf").write_text("Sensitive data")

        # Create a raw log file that should be excluded
        (self.project_root / "data" / "interaction_logs" / "raw_logs.csv").write_text("sensitive raw data")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_should_exclude_sensitive_data(self):
        """Test that sensitive data is excluded."""
        # Test consent directory
        tarinfo_consent = MagicMock()
        tarinfo_consent.name = "data/consent/consent_form.pdf"
        self.assertTrue(should_exclude(tarinfo_consent, self.project_root))

        # Test raw logs
        tarinfo_raw = MagicMock()
        tarinfo_raw.name = "data/interaction_logs/raw_logs.csv"
        self.assertTrue(should_exclude(tarinfo_raw, self.project_root))

        # Test __pycache__
        tarinfo_cache = MagicMock()
        tarinfo_cache.name = "code/utils/__pycache__/module.cpython-39.pyc"
        self.assertTrue(should_exclude(tarinfo_cache, self.project_root))

    def test_should_include_required_files(self):
        """Test that required files are included."""
        # Test results.csv
        tarinfo_results = MagicMock()
        tarinfo_results.name = "data/analysis_results/results.csv"
        self.assertFalse(should_exclude(tarinfo_results, self.project_root))

        # Test anonymized_logs.csv
        tarinfo_anon = MagicMock()
        tarinfo_anon.name = "data/interaction_logs/anonymized_logs.csv"
        self.assertFalse(should_exclude(tarinfo_anon, self.project_root))

        # Test README.md
        tarinfo_readme = MagicMock()
        tarinfo_readme.name = "README.md"
        self.assertFalse(should_exclude(tarinfo_readme, self.project_root))

    def test_create_package_structure(self):
        """Test that the package is created with correct structure."""
        output_path = Path(self.temp_dir) / "test_package.tar.gz"

        package_path = create_reproducibility_package(output_path, self.project_root)

        # Verify package exists
        self.assertTrue(Path(package_path).exists())

        # Verify it's a valid tar.gz
        self.assertTrue(tarfile.is_tarfile(package_path))

        # Verify required files are in the archive
        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()

            # Check for required files
            self.assertIn("README.md", names)
            self.assertIn("data/analysis_results/results.csv", names)
            self.assertIn("data/interaction_logs/anonymized_logs.csv", names)
            self.assertIn("code/analysis", names[0])  # Directory should be present

            # Check that sensitive files are NOT in the archive
            for name in names:
                self.assertNotIn("data/consent", name, f"Sensitive data found in package: {name}")
                self.assertNotIn("raw_logs.csv", name, f"Raw logs found in package: {name}")

    def test_package_contains_analysis_scripts(self):
        """Test that analysis scripts are included."""
        output_path = Path(self.temp_dir) / "test_package.tar.gz"

        # Create a dummy analysis script
        (self.project_root / "code" / "analysis" / "run_statistics.py").write_text("# Dummy script")

        package_path = create_reproducibility_package(output_path, self.project_root)

        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()
            self.assertTrue(any("code/analysis/run_statistics.py" in name for name in names))

    def test_package_contains_tests(self):
        """Test that test files are included."""
        output_path = Path(self.temp_dir) / "test_package.tar.gz"

        # Create a dummy test file
        (self.project_root / "code" / "tests" / "test_statistics.py").write_text("# Dummy test")

        package_path = create_reproducibility_package(output_path, self.project_root)

        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()
            self.assertTrue(any("code/tests/test_statistics.py" in name for name in names))


if __name__ == "__main__":
    unittest.main()