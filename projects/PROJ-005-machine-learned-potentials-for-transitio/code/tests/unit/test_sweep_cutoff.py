"""
Unit tests for sweep_cutoff.py sensitivity analysis logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest

from src.data.sweep_cutoff import (
    analyze_cutoff,
    parse_atomic_features,
    run_sensitivity_analysis,
    CUTOFF_VALUES
)

class TestAnalyzeCutoff:
    def test_empty_graph(self):
        """Test handling of a graph with 0 nodes."""
        atomic_numbers = np.array([])
        positions = np.array([]).reshape(0, 3)
        
        result = analyze_cutoff(atomic_numbers, positions, 3.5)
        
        assert result["num_nodes"] == 0
        assert result["num_edges"] == 0
        assert result["density"] == 0.0
        assert result["avg_coordination"] == 0.0

    def test_single_node(self):
        """Test handling of a graph with 1 node."""
        atomic_numbers = np.array([6])  # Carbon
        positions = np.array([[0.0, 0.0, 0.0]])
        
        result = analyze_cutoff(atomic_numbers, positions, 3.5)
        
        assert result["num_nodes"] == 1
        assert result["num_edges"] == 0
        assert result["density"] == 0.0
        assert result["avg_coordination"] == 0.0

    def test_two_nodes_within_cutoff(self):
        """Test graph with two nodes within cutoff distance."""
        atomic_numbers = np.array([6, 6])
        positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])  # 2.0 Angstroms apart
        
        result = analyze_cutoff(atomic_numbers, positions, 2.5)
        
        assert result["num_nodes"] == 2
        assert result["num_edges"] == 1
        assert result["density"] == 1.0  # Max edges for 2 nodes is 1
        assert result["avg_coordination"] == 1.0
        assert result["max_coordination"] == 1

    def test_two_nodes_outside_cutoff(self):
        """Test graph with two nodes outside cutoff distance."""
        atomic_numbers = np.array([6, 6])
        positions = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]])  # 4.0 Angstroms apart
        
        result = analyze_cutoff(atomic_numbers, positions, 3.5)
        
        assert result["num_nodes"] == 2
        assert result["num_edges"] == 0
        assert result["density"] == 0.0
        assert result["avg_coordination"] == 0.0

    def test_stability_score_calculation(self):
        """Test that stability score is calculated correctly."""
        # Create a graph with uniform edge lengths (perfect stability)
        atomic_numbers = np.array([6, 6, 6])
        # Equilateral triangle with side ~2.0
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [1.0, np.sqrt(3.0), 0.0]
        ])
        
        result = analyze_cutoff(atomic_numbers, positions, 2.5)
        
        # Variance should be 0 (or near 0 due to float precision)
        assert result["feature_stability_score"] >= 0.9  # High stability
        assert result["num_edges"] == 3

class TestParseAtomicFeatures:
    def test_parse_valid_row(self):
        """Test parsing a valid row from the dataframe."""
        row_data = {
            'atomic_numbers': [6, 7, 8],
            'positions': [[0, 0, 0], [1, 1, 1], [2, 2, 2]]
        }
        row = MagicMock()
        row.__getitem__ = lambda self, key: row_data[key]
        
        atomic_numbers, positions = parse_atomic_features(row)
        
        assert isinstance(atomic_numbers, np.ndarray)
        assert isinstance(positions, np.ndarray)
        assert len(atomic_numbers) == 3
        assert positions.shape == (3, 3)

class TestRunSensitivityAnalysis:
    def test_run_on_mock_dataframe(self):
        """Test running the analysis on a mock dataframe."""
        # Create a mock dataframe
        data = {
            'atomic_numbers': [
                [6, 6],
                [6, 6, 6]
            ],
            'positions': [
                [[0, 0, 0], [2, 0, 0]],
                [[0, 0, 0], [2, 0, 0], [1, 1.732, 0]]
            ]
        }
        df = pd.DataFrame(data)
        
        results = run_sensitivity_analysis(df)
        
        assert isinstance(results, list)
        assert len(results) == len(CUTOFF_VALUES)
        
        # Check structure of first result
        first_result = results[0]
        assert "cutoff" in first_result
        assert "avg_num_nodes" in first_result
        assert "avg_density" in first_result
        
        # Verify cutoff value matches
        assert first_result["cutoff"] in CUTOFF_VALUES
        assert first_result["num_samples_processed"] == 2