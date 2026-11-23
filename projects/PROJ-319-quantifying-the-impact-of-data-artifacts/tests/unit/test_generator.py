"""
Unit tests for the synthetic nebula generator (T006).
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
from astropy.io import fits
import pytest

from code.synthetic.generator import (
    generate_nebula_base,
    calculate_true_ellipticity,
    calculate_true_asymmetry,
    generate_synthetic_nebula,
    main
)
from code.config import IMAGE_SIZE, GT_METADATA_FILE


class TestGenerator:
    """Tests for the generator module."""

    def test_generate_nebula_base_shape(self):
        """Test that the generated image has the correct shape."""
        shape = (256, 256)
        center = (128, 128)
        ellipticity = 0.3
        position_angle = 0.0
        flux = 1000.0
        seed = 42
        
        image = generate_nebula_base(
            shape=shape,
            center=center,
            ellipticity=ellipticity,
            position_angle=position_angle,
            flux=flux,
            seed=seed
        )
        
        assert image.shape == shape
        assert np.all(image >= 0)

    def test_generate_nebula_base_ellipticity(self):
        """Test that ellipticity affects the image shape."""
        shape = (256, 256)
        center = (128, 128)
        position_angle = 0.0
        flux = 1000.0
        seed = 42
        
        # Circular nebula
        img_circle = generate_nebula_base(shape, center, 0.0, position_angle, flux, seed)
        # Highly elliptical nebula
        img_elliptical = generate_nebula_base(shape, center, 0.8, position_angle, flux, seed)
        
        # Calculate moments to verify shape difference
        # For a simple check, we can look at the variance along axes
        var_circle_x = np.var(img_circle, axis=0).sum()
        var_circle_y = np.var(img_circle, axis=1).sum()
        
        var_ellip_x = np.var(img_elliptical, axis=0).sum()
        var_ellip_y = np.var(img_elliptical, axis=1).sum()
        
        # The elliptical one should have significantly different variances
        # compared to the circular one (which should be roughly equal)
        ratio_circle = var_circle_x / (var_circle_y + 1e-10)
        ratio_ellip = var_ellip_x / (var_ellip_y + 1e-10)
        
        # Circular should be close to 1, elliptical should deviate
        assert 0.8 < ratio_circle < 1.2
        # The elliptical one should be different (either > 1.5 or < 0.5)
        assert (ratio_ellip > 1.5 or ratio_ellip < 0.5)

    def test_calculate_true_ellipticity(self):
        """Test ellipticity calculation from axes."""
        # Circle: a=b -> e=0
        assert calculate_true_ellipticity(10.0, 10.0) == 0.0
        
        # Ellipse: a=10, b=5 -> e=0.5
        assert calculate_true_ellipticity(10.0, 5.0) == 0.5
        
        # Edge case: very flat
        assert abs(calculate_true_ellipticity(10.0, 1.0) - 0.9) < 1e-6

    def test_calculate_true_asymmetry(self):
        """Test asymmetry calculation."""
        shape = (100, 100)
        center = (50, 50)
        
        # Create a perfectly symmetric image (Gaussian)
        y, x = np.ogrid[:shape[0], :shape[1]]
        image = np.exp(-((x - 50)**2 + (y - 50)**2) / 50)
        
        asymmetry = calculate_true_asymmetry(image, center, seed=42)
        
        # Should be very close to 0 for a symmetric Gaussian
        assert asymmetry < 0.01

    def test_generate_synthetic_nebula_output(self):
        """Test that generate_synthetic_nebula returns correct types."""
        image, gt = generate_synthetic_nebula(
            image_id=0,
            shape=IMAGE_SIZE,
            seed=42
        )
        
        assert isinstance(image, np.ndarray)
        assert image.shape == IMAGE_SIZE
        
        assert isinstance(gt, dict)
        assert "image_id" in gt
        assert "filename" in gt
        assert "ellipticity" in gt
        assert "asymmetry" in gt
        assert "checksum" in gt
        
        # Check ranges
        assert 0.0 <= gt["ellipticity"] <= 1.0
        assert gt["asymmetry"] >= 0.0

    def test_main_creates_files(self):
        """Test that main() creates the expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            n_images = 5
            
            main(n_images=n_images, output_dir=str(output_dir), seed=42)
            
            # Check that files were created
            assert (output_dir / GT_METADATA_FILE).exists()
            
            for i in range(n_images):
                filename = f"synth_{i:03d}.fits"
                assert (output_dir / filename).exists()
            
            # Check metadata content
            with open(output_dir / GT_METADATA_FILE, 'r') as f:
                metadata = json.load(f)
            
            assert len(metadata) == n_images
            for i, entry in enumerate(metadata):
                assert entry["image_id"] == f"{i:03d}"
                assert entry["filename"] == f"synth_{i:03d}.fits"
                assert "ellipticity" in entry
                assert "asymmetry" in entry
                assert "checksum" in entry
                assert entry["checksum"] != ""

    def test_main_writes_valid_fits(self):
        """Test that generated FITS files are valid and contain WCS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            main(n_images=2, output_dir=str(output_dir), seed=42)
            
            fits_file = output_dir / "synth_000.fits"
            with fits.open(fits_file) as hdul:
                # Check primary HDU exists
                assert len(hdul) > 0
                
                # Check data shape
                data = hdul[0].data
                assert data.shape == IMAGE_SIZE
                
                # Check WCS header
                assert 'CTYPE1' in hdul[0].header
                assert 'CTYPE2' in hdul[0].header
                assert 'CRPIX1' in hdul[0].header
                assert 'CRPIX2' in hdul[0].header
                assert 'CDELT1' in hdul[0].header
                assert 'CDELT2' in hdul[0].header