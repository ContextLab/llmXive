"""
Unit tests for microstructure generation logic.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the functions to test
from code.data_generation.generate_microstructures import (
    generate_microstructure,
    calculate_topological_metrics,
    save_microstructure
)

class TestMicrostructureGeneration:
    """Tests for the microstructure generation functions."""

    def test_generate_random_microstructure(self):
        """Test generation of random topology microstructure."""
        seed = 42
        density = 0.3
        topology = 'random'
        
        image = generate_microstructure(seed, density, topology)
        
        assert image.shape == (128, 128), "Image size should be 128x128"
        assert image.dtype == np.float32, "Image dtype should be float32"
        assert np.all((image >= 0) & (image <= 1)), "Values should be in [0, 1]"
        
        # Check density is approximately correct
        actual_density = np.sum(image > 0) / (128 * 128)
        assert abs(actual_density - density) < 0.1, f"Actual density {actual_density} too far from target {density}"

    def test_generate_aligned_microstructure(self):
        """Test generation of aligned topology microstructure."""
        seed = 123
        density = 0.5
        topology = 'aligned'
        
        image = generate_microstructure(seed, density, topology)
        
        assert image.shape == (128, 128)
        assert np.all((image >= 0) & (image <= 1))

    def test_generate_clustered_microstructure(self):
        """Test generation of clustered topology microstructure."""
        seed = 456
        density = 0.2
        topology = 'clustered'
        
        image = generate_microstructure(seed, density, topology)
        
        assert image.shape == (128, 128)
        assert np.all((image >= 0) & (image <= 1))

    def test_invalid_density(self):
        """Test that invalid density raises ValueError."""
        with pytest.raises(ValueError):
            generate_microstructure(seed=1, density=1.5, topology='random')
        
        with pytest.raises(ValueError):
            generate_microstructure(seed=1, density=-0.1, topology='random')

    def test_invalid_topology(self):
        """Test that invalid topology raises ValueError."""
        with pytest.raises(ValueError):
            generate_microstructure(seed=1, density=0.3, topology='invalid')

    def test_reproducibility(self):
        """Test that same seed produces same result."""
        seed = 999
        density = 0.4
        topology = 'random'
        
        image1 = generate_microstructure(seed, density, topology)
        image2 = generate_microstructure(seed, density, topology)
        
        assert np.array_equal(image1, image2), "Same seed should produce identical images"

class TestTopologicalMetrics:
    """Tests for topological metrics calculation."""

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly."""
        seed = 777
        density = 0.3
        topology = 'random'
        
        image = generate_microstructure(seed, density, topology)
        metrics = calculate_topological_metrics(image)
        
        assert 'shape_factor' in metrics
        assert 'connectivity' in metrics
        assert isinstance(metrics['shape_factor'], float)
        assert isinstance(metrics['connectivity'], float)
        assert 0 <= metrics['shape_factor'] <= 1
        assert 0 <= metrics['connectivity'] <= 1

    def test_empty_image_metrics(self):
        """Test metrics for empty image."""
        image = np.zeros((128, 128), dtype=np.float32)
        metrics = calculate_topological_metrics(image)
        
        assert metrics['shape_factor'] == 0.0
        assert metrics['connectivity'] == 0.0

    def test_full_image_metrics(self):
        """Test metrics for full image."""
        image = np.ones((128, 128), dtype=np.float32)
        metrics = calculate_topological_metrics(image)
        
        # Should have at least some valid metrics
        assert metrics['shape_factor'] >= 0.0
        assert metrics['connectivity'] >= 0.0

class TestSaveMicrostructure:
    """Tests for saving microstructures."""

    def test_save_and_load(self):
        """Test saving and loading a microstructure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            
            seed = 888
            density = 0.3
            topology = 'random'
            image = generate_microstructure(seed, density, topology)
            metrics = calculate_topological_metrics(image)
            
            metadata = save_microstructure(
                image, output_path, seed, density, topology, metrics
            )
            
            assert output_path.exists(), "Image file should be created"
            assert metadata['seed'] == seed
            assert metadata['density'] == density
            assert metadata['topology_type'] == topology
            assert 'shape_factor' in metadata
            assert 'connectivity' in metadata

    def test_metadata_structure(self):
        """Test that metadata has required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            
            seed = 111
            density = 0.4
            topology = 'aligned'
            image = generate_microstructure(seed, density, topology)
            metrics = calculate_topological_metrics(image)
            
            metadata = save_microstructure(
                image, output_path, seed, density, topology, metrics
            )
            
            required_fields = [
                'seed', 'density', 'topology_type', 
                'shape_factor', 'connectivity', 'image_path', 'image_size'
            ]
            
            for field in required_fields:
                assert field in metadata, f"Metadata missing required field: {field}"