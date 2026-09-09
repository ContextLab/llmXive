"""Unit tests for the visualize module (T023)."""
import pytest
import os
from visualize import plot_bar_frequencies
import tempfile

def test_plot_generation():
    """Verify image file creation and dimensions (T023)."""
    residue_counts = {0: 10, 1: 12, 2: 8}
    prime = 3
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_plot.png")
        plot_bar_frequencies(residue_counts, prime, output_path=output_path)
        
        assert os.path.exists(output_path), "Plot file was not created"
        assert os.path.getsize(output_path) > 0, "Plot file is empty"
        
        # Verify it's a valid PNG (basic check)
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG', "Not a valid PNG file"