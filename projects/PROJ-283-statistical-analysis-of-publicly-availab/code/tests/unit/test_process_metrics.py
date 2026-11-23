import pytest
import json
import os
import tempfile
from pathlib import Path
from src.data.process import calculate_and_save_inclusion_metrics, validate_inclusion_rate

class TestInclusionMetrics:
    """Tests for inclusion metrics calculation and validation."""

    def test_calculate_and_save_inclusion_metrics_success(self, tmp_path):
        """Test successful calculation and saving of inclusion metrics."""
        output_path = tmp_path / "inclusion_metrics.json"
        total_games = 1000
        parsed_games = 975
        
        calculate_and_save_inclusion_metrics(total_games, parsed_games, str(output_path))
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            metrics = json.load(f)
        
        assert metrics['total_games'] == total_games
        assert metrics['parsed_games'] == parsed_games
        assert abs(metrics['inclusion_rate'] - 0.975) < 1e-6

    def test_calculate_and_save_inclusion_metrics_low_rate(self, tmp_path):
        """Test that low inclusion rate raises SystemExit."""
        output_path = tmp_path / "inclusion_metrics.json"
        total_games = 1000
        parsed_games = 900  # 0.90 rate, below 0.95 threshold
        
        with pytest.raises(SystemExit) as exc_info:
            calculate_and_save_inclusion_metrics(total_games, parsed_games, str(output_path))
        
        assert exc_info.value.code == 1

    def test_validate_inclusion_rate_pass(self):
        """Test validation passes for acceptable rate."""
        assert validate_inclusion_rate(1000, 975) is True
        assert validate_inclusion_rate(1000, 950) is True  # Exactly 0.95
        assert validate_inclusion_rate(1000, 951) is True

    def test_validate_inclusion_rate_fail(self):
        """Test validation fails for unacceptable rate."""
        assert validate_inclusion_rate(1000, 949) is False
        assert validate_inclusion_rate(1000, 900) is False
        assert validate_inclusion_rate(1000, 0) is False

    def test_validate_inclusion_rate_zero_total(self):
        """Test validation handles zero total games."""
        assert validate_inclusion_rate(0, 0) is False

    def test_metrics_schema_compliance(self, tmp_path):
        """Test that saved metrics conform to required schema."""
        output_path = tmp_path / "inclusion_metrics.json"
        total_games = 5000
        parsed_games = 4800
        
        calculate_and_save_inclusion_metrics(total_games, parsed_games, str(output_path))
        
        with open(output_path, 'r') as f:
            metrics = json.load(f)
        
        # Check required keys
        assert 'total_games' in metrics
        assert 'parsed_games' in metrics
        assert 'inclusion_rate' in metrics
        
        # Check types
        assert isinstance(metrics['total_games'], int)
        assert isinstance(metrics['parsed_games'], int)
        assert isinstance(metrics['inclusion_rate'], float)
        
        # Check calculation
        expected_rate = parsed_games / total_games
        assert abs(metrics['inclusion_rate'] - expected_rate) < 1e-6