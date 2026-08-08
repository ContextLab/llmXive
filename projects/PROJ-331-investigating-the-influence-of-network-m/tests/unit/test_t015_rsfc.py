import numpy as np
import pytest
import json
from pathlib import Path
import sys
import os

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess import compute_rsfc, compute_global_efficiency, process_connectome
from utils import save_npy, load_npy

class TestComputeRsfc:
    def test_compute_rsfc_shapes(self):
        """Test that rsfc matrix has correct shape."""
        # Create synthetic BOLD data (10 regions, 100 timepoints)
        np.random.seed(42)
        bold = np.random.randn(10, 100)
        
        rsfc = compute_rsfc(bold)
        
        assert rsfc.shape == (10, 10)
        assert rsfc.dtype in [np.float64, np.float32]

    def test_compute_rsfc_values(self):
        """Test that rsfc values are between -1 and 1."""
        np.random.seed(42)
        bold = np.random.randn(5, 50)
        
        rsfc = compute_rsfc(bold)
        
        assert np.all(rsfc <= 1.0)
        assert np.all(rsfc >= -1.0)
        # Diagonal should be 1 (correlation of signal with itself)
        assert np.allclose(np.diag(rsfc), 1.0)

class TestComputeGlobalEfficiency:
    def test_compute_global_efficiency_shapes(self):
        """Test that efficiency is a scalar."""
        adj = np.random.rand(5, 5)
        adj = (adj + adj.T) / 2  # Symmetrize
        np.fill_diagonal(adj, 0)
        
        eff = compute_global_efficiency(adj)
        
        assert isinstance(eff, float)
        
    def test_compute_global_efficiency_complete_graph(self):
        """Test efficiency on a complete graph with uniform weights."""
        # Complete graph with weight 1.0 everywhere (except diagonal)
        n = 4
        adj = np.ones((n, n))
        np.fill_diagonal(adj, 0)
        
        # Distances are all 1.0.
        # Efficiency = (1 / (N*(N-1))) * sum(1/d_ij)
        # sum(1/d_ij) = N*(N-1) * 1 = N*(N-1)
        # Efficiency = 1.0
        
        eff = compute_global_efficiency(adj)
        assert np.isclose(eff, 1.0)

class TestProcessConnectome:
    def test_process_connectome_integration(self, tmp_path):
        """Test the full process_connectome function with mock data."""
        # Prepare mock data
        weighted_adj = np.random.rand(5, 5)
        weighted_adj = (weighted_adj + weighted_adj.T) / 2
        np.fill_diagonal(weighted_adj, 0)
        
        # Create a mock BOLD timeseries
        bold_timeseries = np.random.randn(5, 100)
        
        # Save to tmp_path
        weighted_adj_path = tmp_path / "weighted_adjacency.npy"
        bold_path = tmp_path / "bold_timeseries.npy"
        rsfc_out = tmp_path / "rsfc.npy"
        eff_out = tmp_path / "global_efficiency.json"
        
        save_npy(weighted_adj, weighted_adj_path)
        save_npy(bold_timeseries, bold_path)
        
        # Run process
        result = process_connectome(
            weighted_adj_path=weighted_adj_path,
            rsfc_output_path=rsfc_out,
            efficiency_output_path=eff_out
        )
        
        # Verify outputs
        assert rsfc_out.exists()
        assert eff_out.exists()
        
        # Verify rsfc content
        rsfc_loaded = load_npy(rsfc_out)
        assert rsfc_loaded.shape == (5, 5)
        
        # Verify efficiency content
        with open(eff_out, 'r') as f:
            eff_data = json.load(f)
        
        assert "global_efficiency" in eff_data
        assert "matrix_shape" in eff_data
        assert eff_data["matrix_shape"] == [5, 5]
        
        # Verify efficiency value matches computation
        expected_eff = compute_global_efficiency(weighted_adj)
        assert np.isclose(eff_data["global_efficiency"], expected_eff)

    def test_missing_weighted_adj(self, tmp_path):
        """Test that FileNotFoundError is raised if weighted adjacency is missing."""
        rsfc_out = tmp_path / "rsfc.npy"
        eff_out = tmp_path / "global_efficiency.json"
        
        with pytest.raises(FileNotFoundError):
            process_connectome(
                weighted_adj_path=tmp_path / "nonexistent.npy",
                rsfc_output_path=rsfc_out,
                efficiency_output_path=eff_out
            )

    def test_missing_bold(self, tmp_path):
        """Test that FileNotFoundError is raised if BOLD data is missing."""
        weighted_adj = np.ones((5, 5))
        weighted_adj_path = tmp_path / "weighted_adjacency.npy"
        save_npy(weighted_adj, weighted_adj_path)
        
        rsfc_out = tmp_path / "rsfc.npy"
        eff_out = tmp_path / "global_efficiency.json"
        
        with pytest.raises(FileNotFoundError):
            process_connectome(
                weighted_adj_path=weighted_adj_path,
                rsfc_output_path=rsfc_out,
                efficiency_output_path=eff_out
            )
