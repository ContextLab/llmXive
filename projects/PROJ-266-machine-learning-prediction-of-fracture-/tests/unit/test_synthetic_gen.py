import pytest
import os
import json
import glob
from pathlib import Path
from PIL import Image
import numpy as np

from code.data.synthetic_gen import (
    generate_sample_metadata,
    generate_grain_structure,
    calculate_physics_informed_k_ic,
    generate_dataset,
    K_IC_PARAMS,
    ALLOY_FAMILIES
)

class TestSyntheticGenerator:
    """Unit tests for synthetic microstructure generator."""

    def test_generate_sample_metadata_all_families(self):
        """Test metadata generation for all alloy families."""
        for family in ALLOY_FAMILIES:
            meta = generate_sample_metadata(0, family)
            assert meta['alloy_family'] == family
            assert 'magnification_calibration' in meta
            assert 'section_thickness' in meta
            assert 'k_ic' in meta
            assert 'grain_size' in meta
            assert 'precipitate_density' in meta
            assert meta['magnification_calibration'] >= 1000
            assert meta['magnification_calibration'] <= 5000
            assert meta['section_thickness'] >= 10
            assert meta['section_thickness'] <= 50

    def test_k_ic_formula_parameters(self):
        """Test that K_IC formula uses correct parameters."""
        for family in ALLOY_FAMILIES:
            params = K_IC_PARAMS[family]
            assert 'base_value' in params
            assert 'alpha' in params
            assert 'beta' in params
            
            # Test calculation
            k_ic = calculate_physics_informed_k_ic(family, 20.0, 0.5)
            assert isinstance(k_ic, float)

    def test_generate_grain_structure(self):
        """Test grain structure generation."""
        img = generate_grain_structure(128, 128, num_grains=50, grain_size=10.0, alloy_family='steel')
        assert img.size == (128, 128)
        assert img.mode == 'L'
        
        # Check that image is not empty
        img_array = np.array(img)
        assert img_array.max() > 0
        assert img_array.min() < 255

    def test_generate_dataset_creates_files(self, tmp_path):
        """Test that dataset generation creates required files."""
        output_dir = tmp_path / "test_data"
        num_images = 50
        
        generate_dataset(
            output_dir=str(output_dir),
            num_images=num_images,
            image_size=128
        )
        
        # Check images exist
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) == num_images
        
        # Check metadata file
        metadata_path = output_dir / "metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert len(metadata) == num_images
        
        # Check alloy family distribution
        families = set(m['alloy_family'] for m in metadata)
        assert families == set(ALLOY_FAMILIES)
        
        # Check required fields in metadata
        for m in metadata:
            assert 'magnification_calibration' in m
            assert 'section_thickness' in m
            assert 'alloy_family' in m
            assert 'k_ic' in m

    def test_dataset_minimum_size(self, tmp_path):
        """Test that dataset meets minimum size requirements."""
        output_dir = tmp_path / "large_data"
        num_images = 2000
        
        generate_dataset(
            output_dir=str(output_dir),
            num_images=num_images,
            image_size=128
        )
        
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) >= 2000
        
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert len(metadata) >= 2000
        
        # Verify all alloy families present
        families = set(m['alloy_family'] for m in metadata)
        assert families == {'steel', 'Al', 'Ti'}

    def test_verification_script_logic(self, tmp_path):
        """Test the exact verification logic from tasks.md."""
        output_dir = tmp_path / "verify_data"
        num_images = 2000
        
        generate_dataset(
            output_dir=str(output_dir),
            num_images=num_images,
            image_size=128
        )
        
        # Simulate verification script
        import glob as glob_module
        png_count = len(list(glob_module.glob(str(output_dir / "*.png"))))
        assert png_count >= 2000
        
        with open(output_dir / "metadata.json", 'r') as f:
            meta = json.load(f)
        
        assert len(meta) >= 2000
        
        families = set([m['alloy_family'] for m in meta])
        assert families == {'steel', 'Al', 'Ti'}
        
        assert all('magnification_calibration' in m for m in meta)