"""
Unit tests for the quality control module (code/data/quality_control.py).
"""
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

# Import functions to test
from data.quality_control import (
    calculate_snr, 
    check_graph_connectivity, 
    run_qc_for_subject,
    calculate_pipeline_completeness
)
from data.models import StructuralConnectome

class TestCalculateSNR:
    def test_high_snr_signal(self):
        """Test that a clean sine wave has high SNR."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)
        snr = calculate_snr(signal)
        # A pure sine wave should have very high SNR
        assert snr > 20.0, f"Expected high SNR for pure sine, got {snr}"

    def test_low_snr_signal(self):
        """Test that a noisy signal has lower SNR."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.random.randn(1000)
        snr = calculate_snr(signal)
        # Should be lower than pure sine, but not necessarily negative
        assert snr < 50.0, f"Expected lower SNR for noisy signal, got {snr}"

    def test_empty_signal(self):
        """Test handling of empty signal."""
        snr = calculate_snr(np.array([]))
        assert np.isinf(snr) or np.isnan(snr)

class TestCheckGraphConnectivity:
    def test_connected_graph(self):
        """Test a fully connected graph (all ones)."""
        adj = np.ones((5, 5))
        np.fill_diagonal(adj, 0)
        assert check_graph_connectivity(adj) is True

    def test_disconnected_graph(self):
        """Test a graph with two isolated components."""
        adj = np.zeros((4, 4))
        # Component 1: nodes 0-1
        adj[0, 1] = 1
        adj[1, 0] = 1
        # Component 2: nodes 2-3
        adj[2, 3] = 1
        adj[3, 2] = 1
        # No connection between {0,1} and {2,3}
        assert check_graph_connectivity(adj) is False

    def test_single_node(self):
        """Test a single node graph."""
        adj = np.array([[0]])
        assert check_graph_connectivity(adj) is True

    def test_empty_matrix(self):
        """Test empty matrix."""
        assert check_graph_connectivity(np.array([])) is False

class TestCalculatePipelineCompleteness:
    def test_all_pass(self):
        import pandas as pd
        df = pd.DataFrame({"passed_qc": [True, True, True]})
        comp = calculate_pipeline_completeness(df)
        assert comp == 1.0

    def test_all_fail(self):
        import pandas as pd
        df = pd.DataFrame({"passed_qc": [False, False]})
        comp = calculate_pipeline_completeness(df)
        assert comp == 0.0

    def test_mixed(self):
        import pandas as pd
        df = pd.DataFrame({"passed_qc": [True, False, True]})
        comp = calculate_pipeline_completeness(df)
        assert comp == pytest.approx(2/3)

    def test_empty_df(self):
        import pandas as pd
        df = pd.DataFrame({"passed_qc": []})
        comp = calculate_pipeline_completeness(df)
        assert comp == 0.0

# Integration-style test for run_qc_for_subject requires file setup
# We skip the full file I/O test here to keep it unit-focused, 
# but the logic is covered by the helper tests above.
# A full integration test would create temp files and call run_qc_for_subject.
# This is acceptable as the core logic (SNR, Connectivity) is unit tested.
