import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from preprocess import compute_rsfc, compute_global_efficiency, process_connectome
from utils import save_npy, load_npy, safe_write_json, load_npy


class TestComputeRsfc:
    def test_compute_rsfc_shape(self):
        # Create random time series
        np.random.seed(42)
        ts = np.random.randn(100, 10)  # 100 timepoints, 10 regions
        rsfc = compute_rsfc(ts)
        assert rsfc.shape == (10, 10)
        assert rsfc.dtype == np.float64

    def test_compute_rsfc_diagonal(self):
        # Correlation of a signal with itself is 1
        np.random.seed(42)
        ts = np.random.randn(100, 5)
        rsfc = compute_rsfc(ts)
        np.testing.assert_array_almost_equal(np.diag(rsfc), np.ones(5))

    def test_compute_rsfc_symmetry(self):
        np.random.seed(42)
        ts = np.random.randn(100, 5)
        rsfc = compute_rsfc(ts)
        np.testing.assert_array_almost_equal(rsfc, rsfc.T)


class TestComputeGlobalEfficiency:
    def test_compute_global_efficiency_complete_graph(self):
        # Complete graph with weight 1 everywhere (except diagonal)
        n = 5
        adj = np.ones((n, n))
        np.fill_diagonal(adj, 0)
        eff = compute_global_efficiency(adj)
        # Distance = 1 for all pairs
        # Sum = n*(n-1) * 1
        # Avg = 1
        assert abs(eff - 1.0) < 1e-6

    def test_compute_global_efficiency_empty_graph(self):
        adj = np.zeros((5, 5))
        eff = compute_global_efficiency(adj)
        assert eff == 0.0

    def test_compute_global_efficiency_weighted(self):
        # Higher weights -> shorter distances -> higher efficiency
        n = 5
        adj = np.ones((n, n)) * 2.0
        np.fill_diagonal(adj, 0)
        eff = compute_global_efficiency(adj)
        # Distance = 0.5
        # 1/d = 2
        # Efficiency should be 2.0
        assert abs(eff - 2.0) < 1e-6


class TestProcessConnectome:
    def test_process_connectome_integration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock data
            n_regions = 10
            n_timepoints = 100
            
            # Weighted adjacency
            weighted_adj = np.random.rand(n_regions, n_regions)
            weighted_adj_path = tmpdir / "weighted_adjacency.npy"
            save_npy(weighted_adj_path, weighted_adj)
            
            # Time series
            time_series = np.random.randn(n_timepoints, n_regions)
            ts_path = tmpdir / "bold_time_series.npy"
            save_npy(ts_path, time_series)
            
            # Output paths
            rsfc_path = tmpdir / "rsfc.npy"
            eff_path = tmpdir / "global_efficiency.json"
            
            # Run
            process_connectome(weighted_adj_path, ts_path, rsfc_path, eff_path)
            
            # Verify outputs
            assert rsfc_path.exists()
            assert eff_path.exists()
            
            rsfc_loaded = load_npy(rsfc_path)
            assert rsfc_loaded.shape == (n_regions, n_regions)
            
            with open(eff_path, 'r') as f:
                eff_data = json.load(f)
            
            assert "global_efficiency" in eff_data
            assert isinstance(eff_data["global_efficiency"], float)
            assert eff_data["matrix_shape"] == [n_regions, n_regions]

    def test_process_connectome_missing_weighted_adj(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            missing_path = tmpdir / "missing.npy"
            
            with pytest.raises(FileNotFoundError): # DataNotFoundError usually wraps this or is a subclass
                # We need to check the exact exception type raised by process_connectome
                # In the implementation, we raise DataNotFoundError
                from utils import DataNotFoundError
                process_connectome(
                    missing_path, 
                    tmpdir / "ts.npy", 
                    tmpdir / "out.npy", 
                    tmpdir / "out.json"
                )

    def test_process_connectome_missing_time_series(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            adj_path = tmpdir / "adj.npy"
            save_npy(adj_path, np.zeros((5, 5)))
            
            with pytest.raises(FileNotFoundError):
                from utils import DataNotFoundError
                process_connectome(
                    adj_path,
                    tmpdir / "missing_ts.npy",
                    tmpdir / "out.npy",
                    tmpdir / "out.json"
                )
