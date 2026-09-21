"""
Unit tests for the Dynamic Router logic (US2).

This module tests the contract of `code/analysis/router.py` to ensure:
1. Correct mapping of entropy scores to matrix indices.
2. Proper clamping logic for out-of-range entropy values.
3. Outlier handling defaults to the median index.

Dependencies:
- code/analysis/router.py (must implement `Router` class)
- code/config.py (for entropy bounds configuration)
"""

import pytest
import numpy as np
import json
import sys
import os
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from analysis.router import Router


class TestRouterInit:
    """Tests for Router initialization."""

    def test_init_with_valid_report(self, tmp_path):
        """Router should initialize successfully with a valid clustering report."""
        # Create a mock clustering report
        report = {
            "layers": ["layer_0", "layer_1"],
            "subsets": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            "boundaries": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "matrices": ["mat_0", "mat_1", "mat_2", "mat_3", "mat_4", "mat_5", "mat_6", "mat_7", "mat_8", "mat_9"]
        }
        report_path = tmp_path / "clustering_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)

        config = Config()
        router = Router(report_path, config)

        assert router.layers == report["layers"]
        assert len(router.boundaries) == len(report["boundaries"])
        assert len(router.matrices) == len(report["matrices"])

    def test_init_missing_file(self, tmp_path):
        """Router should raise FileNotFoundError if report is missing."""
        config = Config()
        with pytest.raises(FileNotFoundError):
            Router("non_existent_path.json", config)

    def test_init_invalid_json(self, tmp_path):
        """Router should raise ValueError if JSON is malformed."""
        report_path = tmp_path / "bad.json"
        report_path.write_text("not valid json")
        config = Config()
        with pytest.raises(json.JSONDecodeError):
            Router(str(report_path), config)

    def test_init_missing_keys(self, tmp_path):
        """Router should raise KeyError if required keys are missing."""
        report = {"layers": ["l0"], "matrices": ["m0"]} # Missing boundaries
        report_path = tmp_path / "incomplete.json"
        with open(report_path, "w") as f:
            json.dump(report, f)

        config = Config()
        with pytest.raises(KeyError):
            Router(str(report_path), config)

class TestRouterLookup:
    """Tests for the core lookup logic."""

    @pytest.fixture
    def sample_router(self, tmp_path):
        """Fixture to create a router with known boundaries."""
        # Create boundaries: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] -> 5 bins
        report = {
            "layers": ["l0"],
            "subsets": list(range(5)),
            "boundaries": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "matrices": ["m0", "m1", "m2", "m3", "m4"]
        }
        report_path = tmp_path / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)
        return Router(report_path, Config())

    def test_lookup_within_bounds(self, sample_router):
        """Should return correct index for in-range entropy."""
        # 0.1 falls in bin 0 [0.0, 0.2)
        assert sample_router.get_matrix_index(0.1) == 0
        # 0.3 falls in bin 1 [0.2, 0.4)
        assert sample_router.get_matrix_index(0.3) == 1
        # 0.9 falls in bin 4 [0.8, 1.0]
        assert sample_router.get_matrix_index(0.9) == 4

    def test_lookup_exact_boundary(self, sample_router):
        """Should handle exact boundary values correctly (usually upper bound exclusive, lower inclusive)."""
        # 0.2 is boundary between bin 0 and 1. Depending on implementation, should be 1.
        # Standard np.digitize behavior: bins=[0.2, ...], x=0.2 -> index 1 (if right=False)
        # Let's assume standard binning: [0.0, 0.2) -> 0, [0.2, 0.4) -> 1
        assert sample_router.get_matrix_index(0.2) == 1

    def test_lookup_out_of_range_low(self, sample_router):
        """Should clamp to minimum index (0) for values below min boundary."""
        assert sample_router.get_matrix_index(-0.5) == 0
        assert sample_router.get_matrix_index(-10.0) == 0

    def test_lookup_out_of_range_high(self, sample_router):
        """Should clamp to maximum index (4) for values above max boundary."""
        assert sample_router.get_matrix_index(1.5) == 4
        assert sample_router.get_matrix_index(100.0) == 4

    def test_lookup_nan_handling(self, sample_router):
        """Should handle NaN by returning the median index or a safe default."""
        # NaN usually results in index -1 or error in digitize, need explicit handling
        # The spec says: "fallback to median"
        result = sample_router.get_matrix_index(np.nan)
        # Median of 5 items (0..4) is 2
        assert result == 2

    def test_lookup_inf_handling(self, sample_router):
        """Should handle Inf by clamping."""
        assert sample_router.get_matrix_index(np.inf) == 4
        assert sample_router.get_matrix_index(-np.inf) == 0

class TestRouterBatch:
    """Tests for batch processing."""

    @pytest.fixture
    def sample_router(self, tmp_path):
        report = {
            "layers": ["l0"],
            "subsets": list(range(3)),
            "boundaries": [0.0, 0.5, 1.0],
            "matrices": ["m0", "m1", "m2"]
        }
        report_path = tmp_path / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)
        return Router(report_path, Config())

    def test_batch_lookup(self, sample_router):
        """Should process a list of entropies and return list of indices."""
        entropies = [0.1, 0.6, 0.9, -1.0, 2.0]
        indices = sample_router.get_matrix_indices(entropies)
        
        assert len(indices) == len(entropies)
        assert indices[0] == 0   # 0.1 -> 0
        assert indices[1] == 1   # 0.6 -> 1
        assert indices[2] == 1   # 0.9 -> 1 (clamped to max 1? No, 1.0 is max boundary. 0.9 is in [0.5, 1.0) -> 1)
        assert indices[3] == 0   # -1.0 -> 0 (clamped)
        assert indices[4] == 1   # 2.0 -> 1 (clamped to max index 1)

    def test_batch_empty_list(self, sample_router):
        """Should return empty list for empty input."""
        assert sample_router.get_matrix_indices([]) == []

class TestRouterIntegration:
    """Integration tests ensuring the router works with real file I/O."""

    def test_full_flow(self, tmp_path):
        """Simulate the full flow: create report -> init router -> query."""
        report = {
            "layers": ["block_1", "block_2"],
            "subsets": list(range(16)),
            "boundaries": [i / 16.0 for i in range(17)],
            "matrices": [f"mat_{i}" for i in range(16)]
        }
        report_path = tmp_path / "full_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)

        router = Router(str(report_path), Config())
        
        # Verify structure
        assert len(router.boundaries) == 17
        assert len(router.matrices) == 16

        # Query specific values
        assert router.get_matrix_index(0.0) == 0
        assert router.get_matrix_index(0.5) == 8
        assert router.get_matrix_index(1.0) == 15
        assert router.get_matrix_index(1.5) == 15
        assert router.get_matrix_index(-0.5) == 0