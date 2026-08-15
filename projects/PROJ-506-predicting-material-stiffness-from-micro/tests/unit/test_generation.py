import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the real functions from the project API surface
from code.data_generation.generate_microstructures import (
    generate_microstructure,
    save_microstructure,
    main
)
from code.utils.fft_homogenization import compute_effective_stiffness

class TestMicrostructureGeneration:
    """Unit tests for microstructure generation logic."""

    def test_generate_microstructure_shape(self):
        """Test that generated microstructure has correct dimensions (128x128)."""
        image = generate_microstructure(
            seed=42,
            resolution=128,
            inclusion_density=0.3,
            n_inclusions=10
        )
        assert image.shape == (128, 128), f"Expected (128, 128), got {image.shape}"
        assert image.dtype == np.float64, f"Expected float64, got {image.dtype}"

    def test_generate_microstructure_density_range(self):
        """Test that generated microstructure density is within expected bounds."""
        # Test low density
        image_low = generate_microstructure(
            seed=101,
            resolution=128,
            inclusion_density=0.1,
            n_inclusions=5
        )
        density_low = np.mean(image_low > 0.5)
        # Allow some variance due to discrete pixel representation
        assert 0.05 <= density_low <= 0.25, f"Low density out of bounds: {density_low}"

        # Test high density
        image_high = generate_microstructure(
            seed=102,
            resolution=128,
            inclusion_density=0.7,
            n_inclusions=20
        )
        density_high = np.mean(image_high > 0.5)
        assert 0.6 <= density_high <= 0.85, f"High density out of bounds: {density_high}"

    def test_generate_microstructure_reproducibility(self):
        """Test that same seed produces identical results."""
        image1 = generate_microstructure(
            seed=999,
            resolution=128,
            inclusion_density=0.4,
            n_inclusions=15
        )
        image2 = generate_microstructure(
            seed=999,
            resolution=128,
            inclusion_density=0.4,
            n_inclusions=15
        )
        np.testing.assert_array_equal(image1, image2, "Seed reproducibility failed")

    def test_generate_microstructure_different_seeds(self):
        """Test that different seeds produce different results."""
        image1 = generate_microstructure(
            seed=1000,
            resolution=128,
            inclusion_density=0.5,
            n_inclusions=12
        )
        image2 = generate_microstructure(
            seed=1001,
            resolution=128,
            inclusion_density=0.5,
            n_inclusions=12
        )
        # They should be different with high probability
        assert not np.array_equal(image1, image2), "Different seeds produced identical images"

    def test_save_microstructure_creates_file(self):
        """Test that save_microstructure creates a valid PNG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image = generate_microstructure(
                seed=50,
                resolution=128,
                inclusion_density=0.4,
                n_inclusions=8
            )
            output_path = Path(tmpdir) / "test_micro.png"
            save_microstructure(image, output_path)
            
            assert output_path.exists(), "Output file was not created"
            assert output_path.suffix == ".png", "Output file has wrong extension"
            assert output_path.stat().st_size > 0, "Output file is empty"

    def test_save_microstructure_path_validation(self):
        """Test that save_microstructure handles invalid paths gracefully."""
        image = generate_microstructure(
            seed=51,
            resolution=128,
            inclusion_density=0.4,
            n_inclusions=8
        )
        with pytest.raises((OSError, ValueError)):
            # Try to save to a non-existent directory
            save_microstructure(image, Path("/nonexistent/dir/test.png"))

    def test_generate_microstructure_boundary_values(self):
        """Test edge cases for density and inclusion count."""
        # Very low density
        image = generate_microstructure(
            seed=200,
            resolution=128,
            inclusion_density=0.01,
            n_inclusions=1
        )
        assert image.shape == (128, 128)
        assert np.all((image >= 0.0) & (image <= 1.0))

        # Zero inclusions (should produce empty background)
        image_empty = generate_microstructure(
            seed=201,
            resolution=128,
            inclusion_density=0.0,
            n_inclusions=0
        )
        # Should be all zeros (background) or very close to it
        assert np.mean(image_empty) < 0.05, "Empty microstructure should be mostly background"

    def test_generate_microstructure_with_fft_compatibility(self):
        """Test that generated images are compatible with FFT homogenization."""
        image = generate_microstructure(
            seed=300,
            resolution=128,
            inclusion_density=0.3,
            n_inclusions=10
        )
        # The FFT solver expects a boolean or float mask
        # Verify the image can be used directly
        try:
            stiffness = compute_effective_stiffness(image)
            assert stiffness is not None, "FFT solver returned None"
            assert stiffness.shape == (3, 3), f"Expected (3, 3) stiffness, got {stiffness.shape}"
        except Exception as e:
            pytest.fail(f"Image incompatible with FFT solver: {e}")

    def test_main_function_integration(self):
        """Test the main function CLI entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            # Run main with minimal args
            sys_args = [
                "test_main",
                "--output_dir", str(output_dir),
                "--n_samples", "2",
                "--resolution", "128",
                "--density_range", "0.2", "0.5"
            ]
            
            # Mock sys.argv for main()
            import sys
            original_argv = sys.argv
            sys.argv = sys_args
            
            try:
                main()
            except SystemExit:
                pass  # Expected from argparse
            finally:
                sys.argv = original_argv
            
            # Check that files were created
            files = list(output_dir.glob("micro_*.png"))
            assert len(files) >= 2, f"Expected at least 2 files, found {len(files)}"