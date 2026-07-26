"""
Tests for the feasibility check module (Task T011).

These tests verify that the feasibility check correctly:
1. Fetches pilot metadata
2. Estimates variance and effect size
3. Calculates required sample size
4. Caps N if necessary
5. Generates the feasibility report
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.feasibility import (
    fetch_pilot_metadata,
    estimate_variance_and_effect_size,
    calculate_required_sample_size,
    calculate_max_feasible_chunks,
    generate_feasibility_report,
    write_feasibility_report,
    main
)
from code.utils.logging import PipelineError


class TestFetchPilotMetadata:
    """Tests for fetch_pilot_metadata function."""

    @patch('code.analysis.feasibility.load_dataset')
    def test_fetches_pilot_data_successfully(self, mock_load_dataset):
        """Test that pilot data is fetched successfully."""
        # Mock dataset iterator
        mock_dataset = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.__iter__ = MagicMock(return_value=iter([
            {'path': 'test.py', 'language': 'python', 'size': 1000, 'repo': 'test'},
            {'path': 'test2.py', 'language': 'python', 'size': 2000, 'repo': 'test'},
            {'path': 'test.java', 'language': 'java', 'size': 1500, 'repo': 'test'},
        ]))
        
        mock_load_dataset.return_value = mock_dataset
        mock_dataset.filter.return_value = mock_filtered
        
        pilot_data, estimated_total = fetch_pilot_metadata()
        
        assert len(pilot_data) == 3
        assert pilot_data[0]['language'] == 'python'
        assert pilot_data[2]['language'] == 'java'
        assert estimated_total > 0

    @patch('code.analysis.feasibility.load_dataset')
    def test_handles_empty_dataset(self, mock_load_dataset):
        """Test that empty dataset is handled correctly."""
        mock_dataset = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.__iter__ = MagicMock(return_value=iter([]))
        
        mock_load_dataset.return_value = mock_dataset
        mock_dataset.filter.return_value = mock_filtered
        
        pilot_data, estimated_total = fetch_pilot_metadata()
        
        assert len(pilot_data) == 0
        assert estimated_total > 0

    @patch('code.analysis.feasibility.load_dataset')
    def test_raises_on_fetch_error(self, mock_load_dataset):
        """Test that fetch error raises PipelineError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(PipelineError):
            fetch_pilot_metadata()


class TestEstimateVarianceAndEffectSize:
    """Tests for estimate_variance_and_effect_size function."""

    def test_calculates_variance_correctly(self):
        """Test that variance is calculated correctly."""
        pilot_data = [
            {'size': 100},
            {'size': 200},
            {'size': 300},
            {'size': 400},
            {'size': 500}
        ]
        
        stats = estimate_variance_and_effect_size(pilot_data)
        
        assert 'variance' in stats
        assert 'effect_size' in stats
        assert 'mean' in stats
        assert stats['mean'] == 300.0
        assert stats['variance'] > 0

    def test_handles_insufficient_data(self):
        """Test that insufficient data is handled with defaults."""
        pilot_data = [{'size': 100}]
        
        stats = estimate_variance_and_effect_size(pilot_data)
        
        assert stats['variance'] == 1.0  # Default
        assert stats['effect_size'] == 0.5  # Default

    def test_raises_on_empty_data(self):
        """Test that empty data raises PipelineError."""
        with pytest.raises(PipelineError):
            estimate_variance_and_effect_size([])


class TestCalculateRequiredSampleSize:
    """Tests for calculate_required_sample_size function."""

    def test_calculates_for_medium_effect_size(self):
        """Test sample size calculation for medium effect size."""
        n = calculate_required_sample_size(effect_size=0.5)
        
        assert n > 0
        assert n < 10000  # Reasonable upper bound

    def test_returns_large_number_for_zero_effect(self):
        """Test that zero effect size returns large number."""
        n = calculate_required_sample_size(effect_size=0)
        
        assert n == 1000000

    def test_calculates_for_small_effect_size(self):
        """Test sample size calculation for small effect size."""
        n = calculate_required_sample_size(effect_size=0.2)
        
        assert n > calculate_required_sample_size(effect_size=0.5)


class TestCalculateMaxFeasibleChunks:
    """Tests for calculate_max_feasible_chunks function."""

    def test_returns_positive_integer(self):
        """Test that max feasible chunks is positive."""
        max_n = calculate_max_feasible_chunks()
        
        assert max_n > 0

    def test_considers_time_limit(self):
        """Test that time limit is considered in calculation."""
        # This is a simple test since the function uses constants
        max_n = calculate_max_feasible_chunks()
        
        # Should be less than 6 hours worth of chunks
        assert max_n < 10000  # Conservative upper bound


class TestGenerateFeasibilityReport:
    """Tests for generate_feasibility_report function."""

    def test_caps_n_when_required_exceeds_max(self):
        """Test that N is capped when required exceeds max feasible."""
        report = generate_feasibility_report(
            required_n=1000,
            max_feasible_n=100,
            pilot_stats={'variance': 1.0, 'effect_size': 0.5, 'mean': 1000},
            estimated_total=10000
        )
        
        assert report['status'] == 'capped'
        assert report['capped_N'] == 100
        assert report['power_limitation'] == "Study underpowered; capped to max feasible"
        assert report['proceed_flag'] is True

    def test_reports_feasible_when_within_limit(self):
        """Test that feasible status is reported when within limit."""
        report = generate_feasibility_report(
            required_n=100,
            max_feasible_n=1000,
            pilot_stats={'variance': 1.0, 'effect_size': 0.5, 'mean': 1000},
            estimated_total=10000
        )
        
        assert report['status'] == 'feasible'
        assert report['capped_N'] == 100
        assert report['power_limitation'] is None
        assert report['proceed_flag'] is True


class TestWriteFeasibilityReport:
    """Tests for write_feasibility_report function."""

    def test_writes_valid_json(self, tmp_path):
        """Test that report is written as valid JSON."""
        output_path = tmp_path / "test_report.json"
        report = {
            'status': 'feasible',
            'capped_N': 100,
            'test_field': 'value'
        }
        
        write_feasibility_report(report, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == report

    def test_creates_directories(self, tmp_path):
        """Test that missing directories are created."""
        output_path = tmp_path / "subdir" / "test_report.json"
        report = {'status': 'feasible'}
        
        write_feasibility_report(report, output_path)
        
        assert output_path.exists()


class TestMain:
    """Tests for main function."""

    @patch('code.analysis.feasibility.fetch_pilot_metadata')
    @patch('code.analysis.feasibility.get_config')
    @patch('code.analysis.feasibility.ensure_dirs')
    @patch('code.analysis.feasibility.set_seed')
    @patch('code.analysis.feasibility.write_feasibility_report')
    def test_main_executes_successfully(
        self, 
        mock_write, 
        mock_set_seed, 
        mock_ensure_dirs, 
        mock_get_config, 
        mock_fetch
    ):
        """Test that main executes successfully."""
        # Mock dependencies
        mock_get_config.return_value = {
            'data_results_dir': '/tmp',
            'random_seed': 42
        }
        mock_fetch.return_value = (
            [{'path': 'test.py', 'language': 'python', 'size': 1000, 'repo': 'test'}],
            10000
        )
        
        # Run main
        result = main()
        
        assert result is not None
        assert 'status' in result
        assert 'capped_N' in result
        assert 'proceed_flag' in result

    @patch('code.analysis.feasibility.fetch_pilot_metadata')
    def test_main_handles_fetch_failure(self, mock_fetch):
        """Test that main handles fetch failure."""
        mock_fetch.side_effect = PipelineError("Fetch failed")
        
        with pytest.raises(PipelineError):
            main()