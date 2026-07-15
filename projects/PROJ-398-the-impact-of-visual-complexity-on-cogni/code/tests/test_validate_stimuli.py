import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.metrics.validate_stimuli import validate_stimuli


class TestValidateStimuli:
    """Unit tests for validate_stimuli functionality."""

    def setup_method(self):
        """Create temporary directory structure for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.stimuli_path = Path(self.temp_dir) / "stimuli"
        self.stimuli_path.mkdir(parents=True)
        self.log_path = Path(self.temp_dir) / "test_validate.log"

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_image(self, name: str, width: int, height: int, valid: bool = True):
        """Helper to create a valid or corrupted image file."""
        if valid:
            # Create a valid dummy image
            img = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.imwrite(str(self.stimuli_path / name), img)
        else:
            # Create a corrupted file (just random bytes)
            with open(self.stimuli_path / name, 'wb') as f:
                f.write(b"not an image data")

    def test_all_valid_images(self):
        """Test that valid images are counted correctly."""
        self._create_image("good1.png", 800, 600)
        self._create_image("good2.jpg", 1920, 1080)
        self._create_image("good3.jpeg", 640, 360)

        results = validate_stimuli(self.stimuli_path, log_file=self.log_path)

        assert results['total'] == 3
        assert results['valid'] == 3
        assert len(results['invalid']) == 0

    def test_undersized_images_rejected(self):
        """Test that images below minimum resolution are rejected."""
        self._create_image("small.png", 320, 240)
        self._create_image("wide_but_tall.jpg", 1000, 200) # Height too low
        self._create_image("tall_but_wide.jpeg", 200, 1000) # Width too low

        results = validate_stimuli(self.stimuli_path, log_file=self.log_path)

        assert results['total'] == 3
        assert results['valid'] == 0
        assert len(results['invalid']) == 3
        
        # Check details
        for item in results['invalid']:
            assert item['reason'] == 'undersized'

    def test_corrupted_images_rejected(self):
        """Test that corrupted files are rejected."""
        self._create_image("corrupted1.png", 800, 600, valid=False)
        self._create_image("corrupted2.jpg", 800, 600, valid=False)

        results = validate_stimuli(self.stimuli_path, log_file=self.log_path)

        assert results['total'] == 2
        assert results['valid'] == 0
        assert len(results['invalid']) == 2

        for item in results['invalid']:
            assert item['reason'] == 'unreadable'

    def test_mixed_results(self):
        """Test a mix of valid, undersized, and corrupted images."""
        self._create_image("valid.png", 800, 600)
        self._create_image("small.jpg", 100, 100)
        self._create_image("corrupt.jpeg", 800, 600, valid=False)
        self._create_image("valid2.bmp", 640, 360) # Exact min size

        results = validate_stimuli(self.stimuli_path, log_file=self.log_path)

        assert results['total'] == 4
        assert results['valid'] == 2
        assert len(results['invalid']) == 2

    def test_log_file_created(self):
        """Test that the log file is created and contains content."""
        self._create_image("test.png", 800, 600)
        
        validate_stimuli(self.stimuli_path, log_file=self.log_path)

        assert self.log_path.exists()
        assert self.log_path.stat().st_size > 0
        content = self.log_path.read_text()
        assert "Validation complete" in content
        assert "PASS: test.png" in content

    def test_empty_directory(self):
        """Test behavior when directory contains no images."""
        results = validate_stimuli(self.stimuli_path, log_file=self.log_path)
        
        assert results['total'] == 0
        assert results['valid'] == 0
        assert len(results['invalid']) == 0
