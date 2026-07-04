"""
Unit tests for the deterministic synthetic tensor generator.
"""
import os
import struct
import tempfile
import json
import numpy as np
import pytest

# Import the module under test
import sys
# Add the code directory to path for imports
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
sys.path.insert(0, code_dir)

from benchmarks.tensor_generator import generate_tensor, save_tensor_to_binary, run_generation

class TestGenerateTensor:
    def test_normal_distribution_shape(self):
        """Test that normal distribution produces correct shape."""
        shape = (10, 20)
        tensor = generate_tensor(shape, distribution="normal", seed=42)
        assert tensor.shape == shape
        assert tensor.dtype == np.float32

    def test_uniform_distribution_shape(self):
        """Test that uniform distribution produces correct shape."""
        shape = (5, 5)
        tensor = generate_tensor(shape, distribution="uniform", seed=42)
        assert tensor.shape == shape

    def test_deterministic_normal(self):
        """Test that same seed produces same normal tensor."""
        shape = (10, 10)
        t1 = generate_tensor(shape, distribution="normal", seed=123)
        t2 = generate_tensor(shape, distribution="normal", seed=123)
        np.testing.assert_array_equal(t1, t2)

    def test_deterministic_uniform(self):
        """Test that same seed produces same uniform tensor."""
        shape = (10, 10)
        t1 = generate_tensor(shape, distribution="uniform", seed=456)
        t2 = generate_tensor(shape, distribution="uniform", seed=456)
        np.testing.assert_array_equal(t1, t2)

    def test_different_seeds_produce_different_tensors(self):
        """Test that different seeds produce different tensors."""
        shape = (10, 10)
        t1 = generate_tensor(shape, distribution="normal", seed=1)
        t2 = generate_tensor(shape, distribution="normal", seed=2)
        assert not np.array_equal(t1, t2)

    def test_invalid_distribution(self):
        """Test that invalid distribution raises ValueError."""
        with pytest.raises(ValueError, match="Invalid distribution type"):
            generate_tensor((10, 10), distribution="invalid")

    def test_normal_values_range(self):
        """Test that normal distribution values are within expected range (mostly)."""
        shape = (1000, 1000)
        tensor = generate_tensor(shape, distribution="normal", seed=42)
        # Most values should be within [-4, 4] for standard normal
        assert np.all(tensor >= -10) and np.all(tensor <= 10)
        assert np.mean(tensor) < 1.0
        assert np.std(tensor) < 2.0

    def test_uniform_values_range(self):
        """Test that uniform distribution values are in [0, 1)."""
        shape = (1000, 1000)
        tensor = generate_tensor(shape, distribution="uniform", seed=42)
        assert np.all(tensor >= 0.0) and np.all(tensor < 1.0)

class TestSaveTensorToBinary:
    def test_save_and_load_normal(self):
        """Test saving and loading a normal tensor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shape = (10, 10)
            tensor = generate_tensor(shape, distribution="normal", seed=42)
            output_path = os.path.join(tmpdir, "test.bin")
            
            # Save
            save_tensor_to_binary(tensor, output_path)
            
            # Load back
            with open(output_path, "rb") as f:
                # Magic
                magic = f.read(4)
                assert magic == b"TENS"
                # Version
                version = struct.unpack("B", f.read(1))[0]
                assert version == 1
                # Dtype
                dtype_char = struct.unpack("B", f.read(1))[0]
                assert chr(dtype_char) == tensor.dtype.char
                # Ndim
                ndim = struct.unpack("B", f.read(1))[0]
                assert ndim == tensor.ndim
                # Shape
                shape_loaded = []
                for _ in range(ndim):
                    shape_loaded.append(struct.unpack("I", f.read(4))[0])
                assert shape_loaded == list(tensor.shape)
                # Data
                data = np.frombuffer(f.read(), dtype=tensor.dtype).reshape(tensor.shape)
                np.testing.assert_array_equal(tensor, data)

    def test_metadata_file_created(self):
        """Test that metadata file is created alongside binary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shape = (5, 5)
            tensor = generate_tensor(shape, distribution="uniform", seed=42)
            output_path = os.path.join(tmpdir, "test.bin")
            metadata = {"test_key": "test_value", "shape": list(shape)}
            
            save_tensor_to_binary(tensor, output_path, metadata)
            
            meta_path = output_path + ".meta"
            assert os.path.exists(meta_path)
            
            with open(meta_path, "r") as f:
                loaded_meta = json.load(f)
            assert loaded_meta["test_key"] == "test_value"
            assert loaded_meta["shape"] == list(shape)

class TestRunGeneration:
    def test_run_generation_creates_files(self):
        """Test that run_generation creates files in the specified directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = [
                {"shape": (10, 10), "distribution": "normal", "seed": 42, "name": "test1"},
                {"shape": (5, 5), "distribution": "uniform", "seed": 43, "name": "test2"},
            ]
            
            results = run_generation(configs, output_dir=tmpdir)
            
            assert len(results) == 2
            for r in results:
                assert os.path.exists(r["path"])
                assert r["path"].endswith(".bin")
                assert os.path.exists(r["path"] + ".meta")

    def test_run_generation_results_structure(self):
        """Test that run_generation returns correct result structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = [
                {"shape": (10, 10), "distribution": "normal", "seed": 42, "name": "test1"},
            ]
            
            results = run_generation(configs, output_dir=tmpdir)
            r = results[0]
            
            assert "path" in r
            assert "shape" in r
            assert "distribution" in r
            assert "seed" in r
            assert "size_bytes" in r
            assert r["shape"] == (10, 10)
            assert r["distribution"] == "normal"
            assert r["seed"] == 42