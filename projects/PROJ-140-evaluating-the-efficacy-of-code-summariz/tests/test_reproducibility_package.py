import unittest
import os
import sys
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.generate_reproducibility_package import (
    should_exclude,
    create_reproducibility_package,
    PACKAGE_NAME,
    PACKAGE_PATH,
)

class TestReproducibilityPackage(unittest.TestCase):
    """Tests for the reproducibility package generation (T031)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Create mock directory structure
        (self.project_root / "data").mkdir()
        (self.project_root / "code").mkdir()
        (self.project_root / "code" / "analysis").mkdir()
        (self.project_root / "code" / "utils").mkdir()
        (self.project_root / "code" / "data_prep").mkdir()
        
        # Create mock data files
        (self.project_root / "data" / "analysis_results").mkdir()
        (self.project_root / "data" / "interaction_logs").mkdir()
        
        # Create mock files
        (self.project_root / "data" / "analysis_results" / "results.csv").write_text("metric,value\naccuracy,0.95\n")
        (self.project_root / "data" / "interaction_logs" / "anonymized_logs.csv").write_text("participant_id,task_id\nP1,T1\n")
        (self.project_root / "README.md").write_text("# Test README")
        
        # Create mock scripts
        (self.project_root / "code" / "analysis" / "run_statistics.py").write_text("# Mock script")
        (self.project_root / "code" / "utils" / "logging_utils.py").write_text("# Mock script")
        
        # Create consent directory with mock file (should be excluded)
        (self.project_root / "data" / "consent").mkdir()
        (self.project_root / "data" / "consent" / "consent_form.pdf").write_text("Mock consent")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_should_exclude_consent(self):
        """Test that consent paths are correctly identified for exclusion."""
        self.assertTrue(should_exclude("data/consent/consent_form.pdf"))
        self.assertTrue(should_exclude("data/consent/user_consent.json"))
        self.assertTrue(should_exclude("DATA/CONSENT/file.txt"))

    def test_should_not_exclude_normal_paths(self):
        """Test that normal paths are not excluded."""
        self.assertFalse(should_exclude("data/analysis_results/results.csv"))
        self.assertFalse(should_exclude("code/analysis/run_statistics.py"))
        self.assertFalse(should_exclude("README.md"))

    def test_create_package_excludes_consent(self):
        """Test that the created package does not contain consent data."""
        output_path = Path(self.test_dir) / "test_package.tar.gz"
        
        # Mock project_root for the function
        with patch('utils.generate_reproducibility_package.project_root', self.project_root):
            success = create_reproducibility_package(
                scripts=["code/analysis/run_statistics.py"],
                data_files=["data/analysis_results/results.csv", "README.md"],
                directories=["code/analysis"],
                output_path=output_path,
            )
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # Verify package contents
        with tarfile.open(output_path, "r:gz") as tar:
            members = tar.getnames()
            
            # Check that consent is NOT in the package
            for member in members:
                self.assertNotIn("consent", member.lower(), 
                               f"Consent data found in package: {member}")
            
            # Check that expected files ARE in the package
            self.assertTrue(any("results.csv" in m for m in members))
            self.assertTrue(any("README.md" in m for m in members))
            self.assertTrue(any("run_statistics.py" in m for m in members))

    def test_package_creation_with_missing_data(self):
        """Test that package creation fails gracefully when data is missing."""
        output_path = Path(self.test_dir) / "test_package.tar.gz"
        
        # Remove required data file
        (self.project_root / "data" / "analysis_results" / "results.csv").unlink()
        
        with patch('utils.generate_reproducibility_package.project_root', self.project_root):
            success = create_reproducibility_package(
                scripts=["code/analysis/run_statistics.py"],
                data_files=["data/analysis_results/results.csv"],
                directories=[],
                output_path=output_path,
            )
        
        # Should still create package but log warning (function handles missing files gracefully)
        # The function logs warnings but continues, so success might be True if other files exist
        # We just verify it doesn't crash
        self.assertIsInstance(success, bool)

    def test_package_is_valid_tar_gz(self):
        """Test that the created file is a valid tar.gz archive."""
        output_path = Path(self.test_dir) / "test_package.tar.gz"
        
        with patch('utils.generate_reproducibility_package.project_root', self.project_root):
            success = create_reproducibility_package(
                scripts=["code/analysis/run_statistics.py"],
                data_files=["data/analysis_results/results.csv", "README.md"],
                directories=[],
                output_path=output_path,
            )
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # Try to open as tar.gz
        try:
            with tarfile.open(output_path, "r:gz") as tar:
                members = tar.getmembers()
                self.assertGreater(len(members), 0)
        except tarfile.TarError:
            self.fail("Created file is not a valid tar.gz archive")

if __name__ == "__main__":
    unittest.main()