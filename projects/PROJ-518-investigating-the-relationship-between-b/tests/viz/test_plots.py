import os
import tempfile
import numpy as np
import pytest
from pathlib import Path
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from viz.plots import plot_flexibility_vs_creativity, compress_image

@pytest.fixture
def sample_data():
    np.random.seed(42)
    flexibility = np.random.normal(0.5, 0.1, 100)
    creativity = 20 * flexibility + np.random.normal(0, 0.5, 100)
    return flexibility, creativity

def test_plot_flexibility_vs_creativity_creates_file(sample_data):
    flexibility, creativity = sample_data
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_plot.png')
        plot_flexibility_vs_creativity(flexibility, creativity, output_path)
        
        assert os.path.exists(output_path), f"Output file {output_path} was not created"
        assert os.path.getsize(output_path) > 0, f"Output file {output_path} is empty"

def test_plot_flexibility_vs_creativity_handles_nan(sample_data):
    flexibility, creativity = sample_data
    # Inject NaN
    flexibility[0] = np.nan
    creativity[1] = np.nan
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_plot_nan.png')
        # Should not raise an error
        plot_flexibility_vs_creativity(flexibility, creativity, output_path)
        
        assert os.path.exists(output_path)

def test_plot_flexibility_vs_creativity_insufficient_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_plot_fail.png')
        with pytest.raises(ValueError):
            plot_flexibility_vs_creativity([1.0], [2.0], output_path)

def test_compress_image_reduces_size():
    # Create a dummy image to compress
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, 'test_img.png')
        plt.figure()
        plt.plot([1, 2, 3])
        plt.savefig(img_path, dpi=300) # High DPI to make it larger
        plt.close()
        
        initial_size = os.path.getsize(img_path)
        compress_image(img_path, max_mb=0.001) # Force compression to very small size
        
        final_size = os.path.getsize(img_path)
        assert final_size < initial_size, "Compression did not reduce file size"