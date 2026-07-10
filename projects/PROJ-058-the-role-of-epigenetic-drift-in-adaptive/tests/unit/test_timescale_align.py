"""
Unit tests for code/analysis/timescale_align.py.

Validates the comparison logic using mock data with known alignment/mismatch scenarios.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.timescale_align import (
    load_timescale_data,
    extract_env_timescale,
    calculate_drift_timescale,
    calculate_alignment_status,
    process_timescale_alignment,
    save_results,
)
from config import get_env

# Mock data fixtures
MOCK_TIMESCALE_DATA = [
    {
        "accession": "GSE001",
        "title": "Multi-gen mouse study",
        "organism": "Mus musculus",
        "fluctuation_timescale": 5.0,  # generations
        "generations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "variance": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "env_type": "temperature",
    },
    {
        "accession": "GSE002",
        "title": "C. elegans nutrient stress",
        "organism": "Caenorhabditis elegans",
        "fluctuation_period": 2.0,  # alternative key
        "generations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "variance": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "env_type": "nutrient",
    },
    {
        "accession": "GSE003",
        "title": "Drosophila constant control",
        "organism": "Drosophila melanogaster",
        "env_period": 10.0,  # third alternative key
        "generations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "variance": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "env_type": "constant",
    },
    {
        "accession": "GSE004",
        "title": "Missing timescale data",
        "organism": "Mus musculus",
        "generations": [1, 2, 3, 4, 5],
        "variance": [0.1, 0.2, 0.3, 0.4, 0.5],
        "env_type": "temperature",
    },
]

# Expected results for mock scenarios
# Drift timescale = slope of variance vs generation
# For GSE001: slope = (1.0 - 0.1) / (10 - 1) = 0.9 / 9 = 0.1 per generation
# Environment timescale = 5.0 generations
# Alignment: drift rate (0.1) vs env frequency (1/5.0 = 0.2)
# But the task defines alignment as: drift rate matches environmental fluctuation frequency within 10%
# Drift timescale = 1/slope = 10 generations (time to accumulate unit variance)
# Env timescale = 5 generations
# Ratio = 10 / 5 = 2.0 -> Mismatched (drift is too slow)

# For GSE003: env_period = 10.0, drift slope = 0.1 -> drift timescale = 10
# Ratio = 10 / 10 = 1.0 -> Aligned

class TestExtractEnvTimescale:
    def test_extract_fluctuation_timescale(self):
        """Test extraction of fluctuation_timescale key."""
        data = {"fluctuation_timescale": 5.0}
        result = extract_env_timescale(data)
        assert result == 5.0

    def test_extract_fluctuation_period(self):
        """Test extraction of fluctuation_period key."""
        data = {"fluctuation_period": 2.0}
        result = extract_env_timescale(data)
        assert result == 2.0

    def test_extract_env_period(self):
        """Test extraction of env_period key."""
        data = {"env_period": 10.0}
        result = extract_env_timescale(data)
        assert result == 10.0

    def test_extract_missing_key(self):
        """Test extraction when no timescale key is present."""
        data = {"other_key": 5.0}
        result = extract_env_timescale(data)
        assert result is None

    def test_extract_priority_order(self):
        """Test that keys are checked in priority order."""
        data = {
            "fluctuation_timescale": 5.0,
            "fluctuation_period": 2.0,
            "env_period": 10.0,
        }
        result = extract_env_timescale(data)
        assert result == 5.0  # Should return first priority key

class TestCalculateDriftTimescale:
    def test_calculate_slope(self):
        """Test drift timescale calculation from variance data."""
        generations = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        variance = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        drift_timescale = calculate_drift_timescale(generations, variance)
        # Slope should be 0.1, so drift timescale = 1/0.1 = 10
        assert abs(drift_timescale - 10.0) < 0.01

    def test_calculate_with_noise(self):
        """Test calculation with noisy variance data."""
        generations = list(range(1, 11))
        variance = [0.1, 0.25, 0.28, 0.42, 0.51, 0.58, 0.72, 0.81, 0.89, 1.05]
        drift_timescale = calculate_drift_timescale(generations, variance)
        assert drift_timescale is not None
        assert drift_timescale > 0

    def test_calculate_zero_variance(self):
        """Test handling of zero variance (should return infinity or None)."""
        generations = [1, 2, 3, 4, 5]
        variance = [0.0, 0.0, 0.0, 0.0, 0.0]
        drift_timescale = calculate_drift_timescale(generations, variance)
        # With zero variance, slope is 0, so drift timescale is infinite
        assert drift_timescale is None or np.isinf(drift_timescale)

    def test_calculate_single_point(self):
        """Test handling of single data point."""
        generations = [1]
        variance = [0.5]
        drift_timescale = calculate_drift_timescale(generations, variance)
        assert drift_timescale is None

class TestCalculateAlignmentStatus:
    def test_aligned_within_10_percent(self):
        """Test alignment when drift and env timescales match within 10%."""
        drift_timescale = 10.0
        env_timescale = 10.0
        status = calculate_alignment_status(drift_timescale, env_timescale)
        assert status == "Aligned"

    def test_aligned_9_percent(self):
        """Test alignment at 9% difference."""
        drift_timescale = 10.0
        env_timescale = 9.1  # ~9% difference
        status = calculate_alignment_status(drift_timescale, env_timescale)
        assert status == "Aligned"

    def test_mismatched_slow(self):
        """Test mismatched status when drift is too slow."""
        drift_timescale = 20.0
        env_timescale = 10.0
        status = calculate_alignment_status(drift_timescale, env_timescale)
        assert status == "Mismatched"

    def test_mismatched_fast(self):
        """Test mismatched status when drift is too fast."""
        drift_timescale = 5.0
        env_timescale = 10.0
        status = calculate_alignment_status(drift_timescale, env_timescale)
        assert status == "Mismatched"

    def test_insufficient_data(self):
        """Test insufficient data when timescales are None."""
        status = calculate_alignment_status(None, 10.0)
        assert status == "Insufficient Data"

        status = calculate_alignment_status(10.0, None)
        assert status == "Insufficient Data"

        status = calculate_alignment_status(None, None)
        assert status == "Insufficient Data"

class TestProcessTimescaleAlignment:
    def test_process_all_scenarios(self):
        """Test processing of multiple mock scenarios."""
        results = process_timescale_alignment(MOCK_TIMESCALE_DATA)

        # Check that we have results for all datasets
        assert len(results) == 4

        # GSE001: drift=10, env=5 -> Mismatched
        gse001 = next(r for r in results if r["accession"] == "GSE001")
        assert gse001["alignment_status"] == "Mismatched"
        assert gse001["temporal_validation_status"] == "VALID"

        # GSE002: drift=10, env=2 -> Mismatched
        gse002 = next(r for r in results if r["accession"] == "GSE002")
        assert gse002["alignment_status"] == "Mismatched"
        assert gse002["temporal_validation_status"] == "VALID"

        # GSE003: drift=10, env=10 -> Aligned
        gse003 = next(r for r in results if r["accession"] == "GSE003")
        assert gse003["alignment_status"] == "Aligned"
        assert gse003["temporal_validation_status"] == "VALID"

        # GSE004: missing env timescale -> Insufficient Data
        gse004 = next(r for r in results if r["accession"] == "GSE004")
        assert gse004["alignment_status"] == "Insufficient Data"
        assert gse004["temporal_validation_status"] == "INSUFFICIENT"

    def test_process_empty_data(self):
        """Test processing of empty dataset list."""
        results = process_timescale_alignment([])
        assert len(results) == 0

    def test_process_partial_data(self):
        """Test processing with partial data (some missing fields)."""
        partial_data = [
            {
                "accession": "GSE005",
                "title": "Partial data",
                "generations": [1, 2, 3],
                "variance": [0.1, 0.2, 0.3],
                # Missing timescale key
            }
        ]
        results = process_timescale_alignment(partial_data)
        assert len(results) == 1
        assert results[0]["alignment_status"] == "Insufficient Data"

class TestSaveResults:
    def test_save_to_file(self):
        """Test saving results to JSON file."""
        results = [
            {
                "accession": "GSE001",
                "alignment_status": "Aligned",
                "temporal_validation_status": "VALID",
                "drift_timescale": 10.0,
                "env_timescale": 10.0,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_alignment.json"
            save_results(results, str(output_path))

            assert output_path.exists()
            with open(output_path, "r") as f:
                loaded = json.load(f)

            assert len(loaded) == 1
            assert loaded[0]["accession"] == "GSE001"

    def test_save_empty_results(self):
        """Test saving empty results list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_empty.json"
            save_results([], str(output_path))

            assert output_path.exists()
            with open(output_path, "r") as f:
                loaded = json.load(f)

            assert len(loaded) == 0

class TestLoadTimescaleData:
    def test_load_from_file(self):
        """Test loading timescale data from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test_input.json"
            with open(input_path, "w") as f:
                json.dump(MOCK_TIMESCALE_DATA, f)

            loaded_data = load_timescale_data(str(input_path))
            assert len(loaded_data) == 4
            assert loaded_data[0]["accession"] == "GSE001"

    def test_load_missing_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_timescale_data("/nonexistent/path.json")

class TestIntegrationScenarios:
    def test_aligned_scenario(self):
        """Integration test for aligned timescale scenario."""
        data = [
            {
                "accession": "TEST001",
                "generations": list(range(1, 11)),
                "variance": [i * 0.1 for i in range(10)],
                "fluctuation_timescale": 10.0,
            }
        ]
        results = process_timescale_alignment(data)
        assert results[0]["alignment_status"] == "Aligned"
        assert results[0]["temporal_validation_status"] == "VALID"

    def test_mismatched_slow_drift(self):
        """Integration test for slow drift scenario."""
        data = [
            {
                "accession": "TEST002",
                "generations": list(range(1, 11)),
                "variance": [i * 0.05 for i in range(10)],  # Slower drift
                "fluctuation_timescale": 5.0,
            }
        ]
        results = process_timescale_alignment(data)
        # Drift timescale = 1/0.05 = 20, env = 5 -> Mismatched
        assert results[0]["alignment_status"] == "Mismatched"
        assert results[0]["temporal_validation_status"] == "VALID"

    def test_mismatched_fast_drift(self):
        """Integration test for fast drift scenario."""
        data = [
            {
                "accession": "TEST003",
                "generations": list(range(1, 11)),
                "variance": [i * 0.2 for i in range(10)],  # Faster drift
                "fluctuation_timescale": 10.0,
            }
        ]
        results = process_timescale_alignment(data)
        # Drift timescale = 1/0.2 = 5, env = 10 -> Mismatched
        assert results[0]["alignment_status"] == "Mismatched"
        assert results[0]["temporal_validation_status"] == "VALID"

    def test_insufficient_data_scenario(self):
        """Integration test for insufficient data scenario."""
        data = [
            {
                "accession": "TEST004",
                "generations": list(range(1, 11)),
                "variance": [i * 0.1 for i in range(10)],
                # No timescale key
            }
        ]
        results = process_timescale_alignment(data)
        assert results[0]["alignment_status"] == "Insufficient Data"
        assert results[0]["temporal_validation_status"] == "INSUFFICIENT"