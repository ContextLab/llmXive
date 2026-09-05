import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from code.data_generation.generate_microstructures import generate_microstructure, save_microstructure

class TestMicrostructureGeneration:
    def test_generate_random_topo(self):
        """Test generation of random topology microstructure."""
        image, metadata = generate_microstructure(
            seed=42,
            topology_type="random",
            inclusion_density=0.3,
            size=128
        )
        
        assert image.shape == (128, 128)
        assert image.dtype == np.uint8
        assert np.all(np.isin(image, [0, 1]))
        assert metadata["topology_type"] == "random"
        assert metadata["seed"] == 42
        # Density should be close to target (allowing for discrete pixel approximation)
        assert 0.25 <= metadata["inclusion_density"] <= 0.35

    def test_generate_aligned_topo(self):
        """Test generation of aligned topology microstructure."""
        image, metadata = generate_microstructure(
            seed=123,
            topology_type="aligned",
            inclusion_density=0.5,
            size=128
        )
        
        assert image.shape == (128, 128)
        assert metadata["topology_type"] == "aligned"
        assert 0.45 <= metadata["inclusion_density"] <= 0.55

    def test_generate_percolating_topo(self):
        """Test generation of percolating topology microstructure."""
        image, metadata = generate_microstructure(
            seed=999,
            topology_type="percolating",
            inclusion_density=0.6,
            size=128
        )
        
        assert image.shape == (128, 128)
        assert metadata["topology_type"] == "percolating"
        assert 0.55 <= metadata["inclusion_density"] <= 0.65

    def test_invalid_density(self):
        """Test that invalid density raises ValueError."""
        with pytest.raises(ValueError):
            generate_microstructure(
                seed=1,
                topology_type="random",
                inclusion_density=1.5
            )
        with pytest.raises(ValueError):
            generate_microstructure(
                seed=1,
                topology_type="random",
                inclusion_density=-0.1
            )

    def test_invalid_topology(self):
        """Test that invalid topology raises ValueError."""
        with pytest.raises(ValueError):
            generate_microstructure(
                seed=1,
                topology_type="invalid",
                inclusion_density=0.3
            )

    def test_topological_metrics_included(self):
        """Test that shape_factor and connectivity are calculated and present in metadata."""
        image, metadata = generate_microstructure(
            seed=42,
            topology_type="random",
            inclusion_density=0.3,
            size=128
        )
        
        assert "shape_factor" in metadata
        assert "connectivity" in metadata
        # shape_factor should be a positive number
        assert isinstance(metadata["shape_factor"], (int, float))
        assert metadata["shape_factor"] > 0
        # connectivity should be an integer (Euler number)
        assert isinstance(metadata["connectivity"], (int, np.integer))

    def test_save_microstructure(self):
        """Test saving microstructure to disk."""
        image, metadata = generate_microstructure(
            seed=42,
            topology_type="random",
            inclusion_density=0.3,
            size=128
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            image_path = save_microstructure(image, metadata, output_dir, 42)
            
            assert Path(image_path).exists()
            assert image_path.endswith("micro_42.png")
            
            # Verify metadata file creation logic (not full file, just check path exists)
            metadata_path = output_dir / "metadata.json"
            # Note: main() creates the metadata file, this test just checks save function
            # We can verify the image loads correctly
            from skimage import io
            loaded = io.imread(image_path)
            assert np.array_equal(loaded, image)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])