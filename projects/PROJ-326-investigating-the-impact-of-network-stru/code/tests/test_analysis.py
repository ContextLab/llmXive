"""
Unit tests for the sensitivity analysis module.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from code.src.analysis.sensitivity import (
    load_simulation_data,
    filter_by_clustering_threshold,
    compute_sensitivity_metrics,
    run_sensitivity_sweep,
    save_sensitivity_results
)


@pytest.fixture
def sample_simulation_data():
    """Create sample simulation data for testing."""
    return [
        {
            "network_id": "net_001",
            "clustering_coefficient": 0.15,
            "diffusion_rate": 0.45,
            "topology_class": "erdos_renyi"
        },
        {
            "network_id": "net_002",
            "clustering_coefficient": 0.25,
            "diffusion_rate": 0.52,
            "topology_class": "watts_strogatz"
        },
        {
            "network_id": "net_003",
            "clustering_coefficient": 0.35,
            "diffusion_rate": 0.48,
            "topology_class": "erdos_renyi"
        },
        {
            "network_id": "net_004",
            "clustering_coefficient": 0.45,
            "diffusion_rate": 0.61,
            "topology_class": "barabasi_albert"
        },
        {
            "network_id": "net_005",
            "clustering_coefficient": 0.55,
            "diffusion_rate": 0.58,
            "topology_class": "watts_strogatz"
        },
        {
            "network_id": "net_006",
            "clustering_coefficient": 0.65,
            "diffusion_rate": 0.72,
            "topology_class": "barabasi_albert"
        },
        {
            "network_id": "net_007",
            "clustering_coefficient": 0.75,
            "diffusion_rate": 0.68,
            "topology_class": "erdos_renyi"
        },
        {
            "network_id": "net_008",
            "clustering_coefficient": 0.85,
            "diffusion_rate": 0.81,
            "topology_class": "watts_strogatz"
        }
    ]


@pytest.fixture
def temp_results_file(sample_simulation_data):
    """Create a temporary file with sample simulation data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_simulation_data, f)
        return Path(f.name)


class TestSensitivitySweepLogic:
    """Tests for the sensitivity sweep logic."""

    def test_load_simulation_data_success(self, temp_results_file):
        """Test successful loading of simulation data."""
        df = load_simulation_data(temp_results_file)
        assert len(df) == 8
        assert "clustering_coefficient" in df.columns
        assert "diffusion_rate" in df.columns
        assert "topology_class" in df.columns

    def test_load_simulation_data_missing_file(self):
        """Test that loading missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_simulation_data(Path("nonexistent_file.json"))

    def test_filter_by_clustering_threshold_ge(self, sample_simulation_data):
        """Test filtering with >= operator."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        filtered = filter_by_clustering_threshold(df, 0.4, operator="ge")
        assert len(filtered) == 5
        assert all(filtered["clustering_coefficient"] >= 0.4)

    def test_filter_by_clustering_threshold_le(self, sample_simulation_data):
        """Test filtering with <= operator."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        filtered = filter_by_clustering_threshold(df, 0.4, operator="le")
        assert len(filtered) == 4
        assert all(filtered["clustering_coefficient"] <= 0.4)

    def test_filter_by_clustering_threshold_invalid_operator(self, sample_simulation_data):
        """Test that invalid operator raises ValueError."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        with pytest.raises(ValueError):
            filter_by_clustering_threshold(df, 0.4, operator="invalid")

    def test_compute_sensitivity_metrics(self, sample_simulation_data):
        """Test computation of sensitivity metrics."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        filtered_df = filter_by_clustering_threshold(df, 0.4, operator="ge")
        metrics = compute_sensitivity_metrics(filtered_df, 0.4)

        assert metrics["threshold"] == 0.4
        assert metrics["sample_size"] == 5
        assert "mean_diffusion_rate" in metrics
        assert "std_diffusion_rate" in metrics
        assert metrics["variance"] >= 0

    def test_run_sensitivity_sweep_minimum_thresholds(self, sample_simulation_data):
        """Test that run_sensitivity_sweep requires at least 5 thresholds."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        with pytest.raises(ValueError) as exc_info:
            run_sensitivity_sweep(df, thresholds=[0.1, 0.2, 0.3])
        assert "at least 5 distinct cutoffs" in str(exc_info.value)

    def test_run_sensitivity_sweep_valid_thresholds(self, sample_simulation_data):
        """Test successful sensitivity sweep with valid thresholds."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            results = run_sensitivity_sweep(df, thresholds=thresholds, output_path=output_path)

            assert len(results) == 5
            assert all(r["sample_size"] >= 0 for r in results)
            assert all(0.0 <= r["threshold"] <= 1.0 for r in results)

            # Verify file was created
            assert output_path.exists()

            # Verify file content
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "results" in data
            assert len(data["results"]) == 5
            assert data["verification"]["meets_sc005"] is True

        finally:
            output_path.unlink(missing_ok=True)

    def test_run_sensitivity_sweep_invalid_threshold_range(self, sample_simulation_data):
        """Test that invalid threshold range raises ValueError."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        with pytest.raises(ValueError):
            run_sensitivity_sweep(df, thresholds=[0.0, 0.2, 0.4, 0.6, 1.5])

    def test_save_sensitivity_results_validation(self, sample_simulation_data):
        """Test that save_sensitivity_results validates minimum cutoffs."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create results with fewer than 5 cutoffs
            results = [
                {"threshold": 0.1, "sample_size": 5},
                {"threshold": 0.2, "sample_size": 4}
            ]

            with pytest.raises(ValueError) as exc_info:
                save_sensitivity_results(results, output_path)

            assert "at least 5 cutoffs" in str(exc_info.value)

        finally:
            output_path.unlink(missing_ok=True)

    def test_sensitivity_sweep_output_structure(self, sample_simulation_data):
        """Test that sensitivity sweep output has correct structure."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            run_sensitivity_sweep(df, thresholds=thresholds, output_path=output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Verify structure
            assert "sweep_parameters" in data
            assert "results" in data
            assert "verification" in data
            assert "metadata" in data

            # Verify sweep_parameters
            assert data["sweep_parameters"]["num_thresholds"] == 5
            assert data["sweep_parameters"]["operator"] == "ge"

            # Verify verification
            assert data["verification"]["meets_sc005"] is True
            assert data["verification"]["all_thresholds_distinct"] is True

        finally:
            output_path.unlink(missing_ok=True)

    def test_empty_filtered_data_handling(self, sample_simulation_data):
        """Test that empty filtered data is handled gracefully."""
        import pandas as pd
        df = pd.DataFrame(sample_simulation_data)
        # Filter with threshold that excludes all data
        filtered_df = filter_by_clustering_threshold(df, 1.0, operator="ge")

        metrics = compute_sensitivity_metrics(filtered_df, 1.0)

        assert metrics["sample_size"] == 0
        assert np.isnan(metrics["mean_diffusion_rate"])
        assert np.isnan(metrics["std_diffusion_rate"])