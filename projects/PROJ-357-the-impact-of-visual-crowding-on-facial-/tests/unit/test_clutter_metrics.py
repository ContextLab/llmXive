import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os
from PIL import Image

# Import the module under test
from utils.clutter_metrics import (
    compute_local_contrast_variance,
    compute_spatial_frequency_energy,
    determine_flanker_region,
    process_stimulus_image
)

class TestLocalContrastVariance:
    def test_uniform_image_zero_variance(self):
        """Uniform image should have near-zero contrast variance."""
        # Create a uniform grayscale image
        img = np.ones((100, 100), dtype=np.uint8) * 128
        region = (10, 90, 10, 90)
        
        variance = compute_local_contrast_variance(img, region)
        assert variance == 0.0, f"Expected 0.0 for uniform image, got {variance}"
    
    def test_gradient_image_positive_variance(self):
        """Gradient image should have positive contrast variance."""
        # Create a gradient image
        img = np.zeros((100, 100), dtype=np.uint8)
        for i in range(100):
            img[:, i] = int(i * 2.55)
        
        region = (10, 90, 10, 90)
        variance = compute_local_contrast_variance(img, region)
        assert variance > 0, f"Expected positive variance for gradient, got {variance}"
    
    def test_color_image_conversion(self):
        """Function should handle color images correctly."""
        # Create a color image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 0] = 255  # Red channel
        
        region = (10, 90, 10, 90)
        variance = compute_local_contrast_variance(img, region)
        assert isinstance(variance, float), "Variance should be a float"

class TestSpatialFrequencyEnergy:
    def test_uniform_image_low_energy(self):
        """Uniform image should have low spatial frequency energy."""
        img = np.ones((64, 64), dtype=np.uint8) * 128
        region = (10, 54, 10, 54)
        
        energy = compute_spatial_frequency_energy(img, region)
        # DC component will be non-zero, but higher frequencies should be minimal
        assert energy >= 0, "Energy should be non-negative"
    
    def test_checkerboard_high_energy(self):
        """Checkerboard pattern should have high spatial frequency energy."""
        # Create a checkerboard pattern
        img = np.zeros((64, 64), dtype=np.uint8)
        for i in range(64):
            for j in range(64):
                if (i // 8 + j // 8) % 2 == 0:
                    img[i, j] = 255
        
        region = (10, 54, 10, 54)
        energy = compute_spatial_frequency_energy(img, region)
        assert energy > 0, "Checkerboard should have positive energy"
    
    def test_empty_region_zero_energy(self):
        """Empty region should return zero energy."""
        img = np.ones((100, 100), dtype=np.uint8) * 128
        region = (0, 0, 0, 0)  # Empty region
        
        energy = compute_spatial_frequency_energy(img, region)
        assert energy == 0.0, f"Expected 0.0 for empty region, got {energy}"

class TestFlankerRegionDetermination:
    def test_region_bounds_within_image(self):
        """Flanker region should be within image bounds."""
        shape = (200, 200, 3)
        eccentricity = 50.0
        flanker_count = 8
        
        region = determine_flanker_region(shape, eccentricity, flanker_count)
        y_min, y_max, x_min, x_max = region
        
        assert y_min >= 0 and y_max <= shape[0], "Y bounds exceed image height"
        assert x_min >= 0 and x_max <= shape[1], "X bounds exceed image width"
        assert y_max > y_min and x_max > x_min, "Region should have positive dimensions"
    
    def test_eccentricity_affects_region_size(self):
        """Higher eccentricity should result in larger flanker region."""
        shape = (200, 200, 3)
        flanker_count = 8
        
        region_low = determine_flanker_region(shape, 10.0, flanker_count)
        region_high = determine_flanker_region(shape, 50.0, flanker_count)
        
        # Higher eccentricity should expand the region
        area_low = (region_low[1] - region_low[0]) * (region_low[3] - region_low[2])
        area_high = (region_high[1] - region_high[0]) * (region_high[3] - region_high[2])
        
        assert area_high >= area_low, "Higher eccentricity should produce larger or equal region"

class TestProcessStimulusImage:
    def setup_method(self):
        """Create temporary test image."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = Path(self.temp_dir) / "test_stimulus.png"
        
        # Create a simple test image
        img = Image.new('RGB', (200, 200), color='red')
        img.save(str(self.test_image_path))
        
        self.manifest_entry = {
            'file_path': 'test_stimulus.png',
            'emotion': 'happy',
            'flanker_count': 8,
            'eccentricity': 30.0
        }
    
    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        os.rmdir(self.temp_dir)
    
    def test_successful_processing(self):
        """Should successfully process a valid image."""
        result = process_stimulus_image(self.test_image_path, self.manifest_entry)
        
        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert result['local_contrast_variance'] is not None
        assert result['spatial_frequency_energy'] is not None
        assert result['flanker_count'] == 8
        assert result['eccentricity'] == 30.0
    
    def test_missing_image_handling(self):
        """Should handle missing image gracefully."""
        missing_path = Path(self.temp_dir) / "nonexistent.png"
        result = process_stimulus_image(missing_path, self.manifest_entry)
        
        assert result['status'] == 'error' or 'error' in result['status'].lower()
        assert result['local_contrast_variance'] is None
        assert result['spatial_frequency_energy'] is None

class TestIntegration:
    def test_full_pipeline_with_temp_manifest(self):
        """Test the full pipeline with a temporary manifest and stimuli."""
        from utils.clutter_metrics import compute_clutter_metrics
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create stimuli directory
            stimuli_dir = temp_path / "stimuli"
            stimuli_dir.mkdir()
            
            # Create test images
            for i in range(3):
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img.save(str(stimuli_dir / f"stimulus_{i}.png"))
            
            # Create manifest
            manifest = {
                "stimuli": [
                    {
                        "file_path": "stimulus_0.png",
                        "emotion": "happy",
                        "flanker_count": 4,
                        "eccentricity": 20.0
                    },
                    {
                        "file_path": "stimulus_1.png",
                        "emotion": "sad",
                        "flanker_count": 8,
                        "eccentricity": 30.0
                    },
                    {
                        "file_path": "stimulus_2.png",
                        "emotion": "angry",
                        "flanker_count": 12,
                        "eccentricity": 40.0
                    }
                ]
            }
            
            manifest_path = temp_path / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            output_path = temp_path / "metrics.csv"
            
            # Run computation
            compute_clutter_metrics(manifest_path, stimuli_dir, output_path, chunk_size=2)
            
            # Verify output
            assert output_path.exists(), "Output CSV should be created"
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            # Check header
            assert "local_contrast_variance" in lines[0]
            assert "spatial_frequency_energy" in lines[0]
            
            # Check data rows (skip header)
            data_lines = lines[1:]
            assert len(data_lines) == 3, f"Expected 3 data rows, got {len(data_lines)}"
            
            # Verify metrics are computed (not empty)
            for line in data_lines:
                parts = line.strip().split(',')
                # Check that variance and energy are not empty strings
                assert parts[1] != '', "Local contrast variance should be computed"
                assert parts[2] != '', "Spatial frequency energy should be computed"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])