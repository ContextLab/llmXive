"""
Unit tests for the fmriprep image pull script (T008b).
"""
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import the function to test
# We assume the script is in the same directory or code/
# Adjust import path if necessary based on execution context
try:
    from pull_fmriprep_image import pull_fmriprep_image, IMAGE_NAME, FMRI_PREP_TAG
except ImportError:
    # Fallback for running tests from root if code/ is not in path
    sys.path.insert(0, 'code')
    from pull_fmriprep_image import pull_fmriprep_image, IMAGE_NAME, FMRI_PREP_TAG


class TestPullFmriprepImage(unittest.TestCase):
    
    def test_image_tag_is_stable(self):
        """Verify that the selected tag is a specific version string."""
        self.assertIsInstance(FMRI_PREP_TAG, str)
        self.assertTrue(len(FMRI_PREP_TAG) > 0)
        # Check it looks like a version number (major.minor.patch)
        parts = FMRI_PREP_TAG.split('.')
        self.assertGreaterEqual(len(parts), 2)
        
    def test_image_name_format(self):
        """Verify the full image name format."""
        expected = f"nipreps/fmriprep:{FMRI_PREP_TAG}"
        self.assertEqual(IMAGE_NAME, expected)

    @patch('pull_fmriprep_image.subprocess.run')
    def test_pull_success(self, mock_run):
        """Test successful pull scenario."""
        mock_run.return_value = MagicMock(returncode=0)
        result = pull_fmriprep_image("nipreps/fmriprep:test")
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('pull_fmriprep_image.subprocess.run')
    def test_pull_failure(self, mock_run):
        """Test failed pull scenario."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "docker pull", output="Error")
        result = pull_fmriprep_image("nipreps/fmriprep:test")
        self.assertFalse(result)

    @patch('pull_fmriprep_image.subprocess.run')
    def test_docker_not_found(self, mock_run):
        """Test when docker command is missing."""
        mock_run.side_effect = FileNotFoundError("docker")
        result = pull_fmriprep_image("nipreps/fmriprep:test")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()