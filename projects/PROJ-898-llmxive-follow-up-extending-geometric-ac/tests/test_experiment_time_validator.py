"""
Unit tests for ExperimentTimeValidator.

Tests cover:
- Budget calculation accuracy
- CI limit validation
- Abort logic enforcement
- Edge cases (zero trials, exact boundary)
"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.experiment_time_validator import (
    ExperimentTimeValidator,
    BudgetResult,
    CI_TIME_LIMIT_SECONDS,
    PER_STEP_TIME_LIMIT_SECONDS
)
from code.config import ExperimentConfig

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = """
    experiment:
      trial_count: 50
      seed: 42
    solver:
      timeout_limits: 300
    topology:
      topology_counts: [1, 2, 3]
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def validator_with_config(temp_config_file):
    """Create a validator instance with the temporary config."""
    return ExperimentTimeValidator(temp_config_file)

class TestExperimentTimeValidator:
    """Test suite for ExperimentTimeValidator class."""

    def test_load_config_success(self, validator_with_config):
        """Test successful configuration loading."""
        assert validator_with_config.config is not None
        assert validator_with_config.config.trial_count == 50
        assert validator_with_config.config.timeout_limits == 300

    def test_load_config_missing_file(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            ExperimentTimeValidator("nonexistent_config.yaml")

    def test_calculate_total_time_default_values(self, validator_with_config):
        """Test total time calculation with default values."""
        # 50 trials * 300s timeout * 1 step/trial = 15000s
        total_time, total_steps = validator_with_config.calculate_total_experiment_time()
        
        assert total_steps == 50
        assert total_time == 15000.0

    def test_calculate_total_time_custom_values(self, validator_with_config):
        """Test total time calculation with custom values."""
        total_time, total_steps = validator_with_config.calculate_total_experiment_time(
            per_step_time=100.0,
            steps_per_trial=2
        )
        
        # 50 trials * 100s * 2 steps = 10000s
        assert total_steps == 100
        assert total_time == 10000.0

    def test_validate_within_budget(self, validator_with_config):
        """Test validation when experiment is within budget."""
        # 50 trials * 100s * 1 step = 5000s (< 6 hours = 21600s)
        result = validator_with_config.validate_against_ci_limit(
            per_step_time=100.0,
            steps_per_trial=1
        )
        
        assert result.is_within_budget is True
        assert result.estimated_total_seconds == 5000.0
        assert result.remaining_seconds == CI_TIME_LIMIT_SECONDS - 5000.0
        assert result.trials_to_abort == 0

    def test_validate_exceeds_budget(self, validator_with_config):
        """Test validation when experiment exceeds budget."""
        # 50 trials * 500s * 1 step = 25000s (> 6 hours = 21600s)
        result = validator_with_config.validate_against_ci_limit(
            per_step_time=500.0,
            steps_per_trial=1
        )
        
        assert result.is_within_budget is False
        assert result.estimated_total_seconds == 25000.0
        assert result.trials_to_abort == 8  # 25000 - 21600 = 3400s excess, 3400/500 ≈ 7 -> 8 trials to abort
        assert result.max_trials_allowed == 42  # 21600/500 = 43.2 -> 42

    def test_validate_exact_boundary(self, validator_with_config):
        """Test validation when experiment is exactly at the limit."""
        # 72 trials * 300s = 21600s (exactly 6 hours)
        # But our config has 50 trials, so we simulate with custom values
        result = validator_with_config.validate_against_ci_limit(
            per_step_time=432.0,  # 21600 / 50 = 432
            steps_per_trial=1
        )
        
        assert result.is_within_budget is True
        assert abs(result.estimated_total_seconds - CI_TIME_LIMIT_SECONDS) < 0.01

    def test_enforce_budget_proceed(self, validator_with_config):
        """Test that trials proceed when within budget."""
        # First trial should proceed
        assert validator_with_config.enforce_budget(
            current_trial=0,
            per_step_time=100.0,
            steps_per_trial=1
        ) is True

        # Trial 40 should still proceed (50 trials * 100s = 5000s < 21600s)
        assert validator_with_config.enforce_budget(
            current_trial=40,
            per_step_time=100.0,
            steps_per_trial=1
        ) is True

    def test_enforce_budget_abort(self, validator_with_config):
        """Test that trials are aborted when exceeding budget."""
        # 50 trials * 500s = 25000s > 21600s
        # Max allowed: 21600/500 = 43.2 -> 43 trials
        # Trial 43 and beyond should be aborted
        
        # Trial 42 should proceed (0-indexed, so 43rd trial)
        assert validator_with_config.enforce_budget(
            current_trial=42,
            per_step_time=500.0,
            steps_per_trial=1
        ) is True

        # Trial 43 should be aborted
        assert validator_with_config.enforce_budget(
            current_trial=43,
            per_step_time=500.0,
            steps_per_trial=1
        ) is False

        # Trial 49 should definitely be aborted
        assert validator_with_config.enforce_budget(
            current_trial=49,
            per_step_time=500.0,
            steps_per_trial=1
        ) is False

    def test_get_abort_recommendation_within_budget(self, validator_with_config):
        """Test abort recommendation when within budget."""
        result = validator_with_config.get_abort_recommendation(
            per_step_time=100.0,
            steps_per_trial=1
        )
        
        assert "✅" in result
        assert "within budget" in result.lower()

    def test_get_abort_recommendation_exceeds_budget(self, validator_with_config):
        """Test abort recommendation when exceeding budget."""
        result = validator_with_config.get_abort_recommendation(
            per_step_time=500.0,
            steps_per_trial=1
        )
        
        assert "⚠️" in result or "WARNING" in result.upper()
        assert "exceeds" in result.lower() or "exceeded" in result.lower()
        assert "abort" in result.lower()

    def test_budget_result_dataclass(self):
        """Test BudgetResult dataclass initialization."""
        result = BudgetResult(
            is_within_budget=True,
            estimated_total_seconds=10000.0,
            remaining_seconds=11600.0,
            max_trials_allowed=50,
            trials_to_abort=0,
            message="Test message"
        )
        
        assert result.is_within_budget is True
        assert result.estimated_total_seconds == 10000.0
        assert result.remaining_seconds == 11600.0
        assert result.max_trials_allowed == 50
        assert result.trials_to_abort == 0
        assert result.message == "Test message"

class TestMainFunction:
    """Test the main function entry point."""

    def test_main_success(self, temp_config_file):
        """Test main function when budget is not exceeded."""
        # Patch sys.exit to capture exit code
        with patch('sys.exit') as mock_exit:
            # Create a validator with low per-step time to stay within budget
            validator = ExperimentTimeValidator(temp_config_file)
            result = validator.validate_against_ci_limit(per_step_time=100.0)
            
            # The main function would exit with 0 if within budget
            # We can't easily test the full main() without mocking logging,
            # but we can verify the logic path
            assert result.is_within_budget is True

    def test_main_failure(self, temp_config_file):
        """Test main function when budget is exceeded."""
        # Create a validator with high per-step time to exceed budget
        validator = ExperimentTimeValidator(temp_config_file)
        result = validator.validate_against_ci_limit(per_step_time=500.0)
        
        assert result.is_within_budget is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])