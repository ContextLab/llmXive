"""
Unit tests for edge cases in the material strength prediction pipeline.
Focus: Corrupted data handling and extreme aspect ratios.
"""
import os
import sys
import tempfile
import json
import cv2
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.preprocess import resize_with_aspect_ratio, normalize_image, preprocess_single_image
from data.validate import validate_image_exists, validate_pair, load_manifest
from utils.config import get_project_root


class TestCorruptedDataHandling:
    """Tests for handling corrupted image files and invalid manifests."""

    def setup_method(self):
        """Create temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_img_path = Path(self.temp_dir) / "test_image.png"
        self.corrupt_img_path = Path(self.temp_dir) / "corrupt_image.png"
        self.empty_img_path = Path(self.temp_dir) / "empty_image.png"

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_corrupted_image_file(self):
        """Test that corrupted image files are detected and handled gracefully."""
        # Create a file that looks like an image but contains garbage
        with open(self.corrupt_img_path, "wb") as f:
            f.write(b"NOT_A_REAL_IMAGE_DATA" + os.urandom(1000))

        # Attempt to preprocess the corrupted image
        # This should either raise a clear error or return a specific failure indicator
        with pytest.raises((cv2.error, OSError, ValueError)):
            preprocess_single_image(self.corrupt_img_path, (224, 224))

    def test_empty_image_file(self):
        """Test that empty image files are detected."""
        # Create an empty file
        with open(self.empty_img_path, "wb") as f:
            pass

        # Attempt to read the empty file
        with pytest.raises((cv2.error, OSError)):
            preprocess_single_image(self.empty_img_path, (224, 224))

    def test_truncated_image_file(self):
        """Test handling of truncated image files."""
        # Create a valid PNG header but truncate the data
        # PNG signature + IHDR chunk + truncated IDAT
        png_sig = b"\x89PNG\r\n\x1a\n"
        ihdr = b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        truncated_data = png_sig + ihdr + b"\x00" * 10  # Truncated IDAT

        with open(self.test_img_path, "wb") as f:
            f.write(truncated_data)

        # Should fail to read
        with pytest.raises((cv2.error, OSError)):
            preprocess_single_image(self.test_img_path, (224, 224))

    def test_malformed_manifest(self):
        """Test validation of malformed manifest files."""
        manifest_path = Path(self.temp_dir) / "malformed_manifest.json"

        # Write malformed JSON
        with open(manifest_path, "w") as f:
            f.write('{"invalid": json, "missing": quotes}')

        # Attempt to load should raise JSON decode error
        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_path)

    def test_missing_image_in_manifest(self):
        """Test validation when image file referenced in manifest is missing."""
        manifest_data = {
            "image_id": "missing_img_001",
            "image_path": "data/processed/nonexistent.png",
            "yield_strength": 250.0
        }

        manifest_path = Path(self.temp_dir) / "missing_img_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)

        # Load manifest and validate
        manifest = load_manifest(manifest_path)
        # validate_image_exists should return False or raise
        assert not validate_image_exists(Path(manifest["image_path"]))


class TestExtremeAspectRatios:
    """Tests for handling images with extreme aspect ratios."""

    def setup_method(self):
        """Create temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_very_wide_image(self):
        """Test processing of extremely wide image (e.g., 10:1 aspect ratio)."""
        # Create a very wide image (1000x100)
        wide_img = np.random.randint(0, 255, (100, 1000, 3), dtype=np.uint8)
        wide_path = Path(self.temp_dir) / "wide_image.png"
        cv2.imwrite(str(wide_path), wide_img)

        # Preprocess should handle this gracefully (resize maintaining aspect ratio)
        processed = preprocess_single_image(wide_path, (224, 224))

        # Output should be 224x224
        assert processed.shape[0] == 224
        assert processed.shape[1] == 224

        # The shorter dimension (100) should be scaled up, wider dimension scaled down
        # Verify no distortion by checking if original aspect ratio is preserved in the crop/padding logic
        # (Actual behavior depends on implementation, but it should not crash)

    def test_very_tall_image(self):
        """Test processing of extremely tall image (e.g., 1:10 aspect ratio)."""
        # Create a very tall image (100x1000)
        tall_img = np.random.randint(0, 255, (1000, 100, 3), dtype=np.uint8)
        tall_path = Path(self.temp_dir) / "tall_image.png"
        cv2.imwrite(str(tall_path), tall_img)

        # Preprocess should handle this gracefully
        processed = preprocess_single_image(tall_path, (224, 224))

        assert processed.shape[0] == 224
        assert processed.shape[1] == 224

    def test_extreme_width_ratio(self):
        """Test resize_with_aspect_ratio with extreme width ratio."""
        # 10000x100 image -> should fit in 224x224 box
        src_w, src_h = 10000, 100
        target_w, target_h = 224, 224

        # Create dummy image
        img = np.random.randint(0, 255, (src_h, src_w, 3), dtype=np.uint8)
        img_path = Path(self.temp_dir) / "extreme_wide.png"
        cv2.imwrite(str(img_path), img)

        # This should not crash
        resized = resize_with_aspect_ratio(img_path, (target_w, target_h))

        # Output should fit within target dimensions
        assert resized.shape[0] <= target_h
        assert resized.shape[1] <= target_w

    def test_extreme_height_ratio(self):
        """Test resize_with_aspect_ratio with extreme height ratio."""
        # 100x10000 image
        src_w, src_h = 100, 10000
        target_w, target_h = 224, 224

        img = np.random.randint(0, 255, (src_h, src_w, 3), dtype=np.uint8)
        img_path = Path(self.temp_dir) / "extreme_tall.png"
        cv2.imwrite(str(img_path), img)

        resized = resize_with_aspect_ratio(img_path, (target_w, target_h))

        assert resized.shape[0] <= target_h
        assert resized.shape[1] <= target_w

    def test_square_to_extreme(self):
        """Test resize from square to extreme target (edge case for logic)."""
        # 224x224 source, target 224x224 (no-op case)
        square_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        square_path = Path(self.temp_dir) / "square.png"
        cv2.imwrite(str(square_path), square_img)

        resized = resize_with_aspect_ratio(square_path, (224, 224))

        assert resized.shape[0] == 224
        assert resized.shape[1] == 224


class TestNormalizationEdgeCases:
    """Tests for normalization with edge case values."""

    def test_all_zeros_image(self):
        """Test normalization of an all-zeros image."""
        zeros_img = np.zeros((224, 224, 3), dtype=np.uint8)
        normalized = normalize_image(zeros_img)

        # Should not crash, result should be zeros or NaN handled
        assert normalized.shape == (224, 224, 3)

    def test_all_ones_image(self):
        """Test normalization of an all-255s image."""
        ones_img = np.full((224, 224, 3), 255, dtype=np.uint8)
        normalized = normalize_image(ones_img)

        assert normalized.shape == (224, 224, 3)

    def test_single_pixel_variance(self):
        """Test normalization with single non-zero pixel."""
        sparse_img = np.zeros((224, 224, 3), dtype=np.uint8)
        sparse_img[100, 100, 0] = 255

        normalized = normalize_image(sparse_img)

        assert normalized.shape == (224, 224, 3)
        # Check that normalization didn't produce inf/nan
        assert not np.any(np.isnan(normalized))
        assert not np.any(np.isinf(normalized))


class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = Path(self.temp_dir) / "edge_case_manifest.json"

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mixed_valid_invalid_manifest(self):
        """Test validation of manifest with mix of valid and invalid entries."""
        # Create one valid image
        valid_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        valid_path = Path(self.temp_dir) / "valid.png"
        cv2.imwrite(str(valid_path), valid_img)

        # Create manifest with valid and invalid entries
        manifest_data = [
            {"image_id": "valid_001", "image_path": str(valid_path), "yield_strength": 250.0},
            {"image_id": "invalid_001", "image_path": "nonexistent.png", "yield_strength": 300.0},
            {"image_id": "corrupt_001", "image_path": "corrupt.png", "yield_strength": 280.0}
        ]

        with open(self.manifest_path, "w") as f:
            json.dump(manifest_data, f)

        # Load and validate
        manifest = load_manifest(self.manifest_path)
        valid_count = 0
        invalid_count = 0

        for entry in manifest:
            if validate_image_exists(Path(entry["image_path"])):
                valid_count += 1
            else:
                invalid_count += 1

        # Should detect 1 valid, 2 invalid
        assert valid_count == 1
        assert invalid_count == 2

    def test_extreme_ratio_manifest(self):
        """Test processing manifest containing extreme aspect ratio images."""
        # Create extreme aspect ratio images
        wide_img = np.random.randint(0, 255, (50, 500, 3), dtype=np.uint8)
        wide_path = Path(self.temp_dir) / "wide.png"
        cv2.imwrite(str(wide_path), wide_img)

        tall_img = np.random.randint(0, 255, (500, 50, 3), dtype=np.uint8)
        tall_path = Path(self.temp_dir) / "tall.png"
        cv2.imwrite(str(tall_path), tall_img)

        manifest_data = [
            {"image_id": "wide_001", "image_path": str(wide_path), "yield_strength": 250.0},
            {"image_id": "tall_001", "image_path": str(tall_path), "yield_strength": 300.0}
        ]

        with open(self.manifest_path, "w") as f:
            json.dump(manifest_data, f)

        # Process should not crash
        manifest = load_manifest(self.manifest_path)
        for entry in manifest:
            img_path = Path(entry["image_path"])
            # This should handle the extreme ratios without error
            processed = preprocess_single_image(img_path, (224, 224))
            assert processed.shape[0] == 224
            assert processed.shape[1] == 224