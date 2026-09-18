"""
Unit tests for the parity checker utility.

These tests verify that the ParityChecker class and related functions
correctly enforce budget constraints and track evaluation statistics.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.parity_checker import (
    ParityError,
    EvaluationStats,
    ParityChecker,
    check_and_enforce_parity,
    verify_run_parity
)


class TestParityError:
    """Tests for the ParityError exception."""

    def test_parity_error_instantiation(self):
        """Test that ParityError can be instantiated with a message."""
        error = ParityError("Test error message")
        assert str(error) == "Test error message"

    def test_parity_error_inherits_exception(self):
        """Test that ParityError is a subclass of Exception."""
        assert issubclass(ParityError, Exception)


class TestEvaluationStats:
    """Tests for the EvaluationStats dataclass."""

    def test_default_values(self):
        """Test default values for EvaluationStats."""
        stats = EvaluationStats()
        assert stats.total_evaluations == 0
        assert stats.budget == 0
        assert stats.condition == ""
        assert stats.current_count == 0

    def test_custom_values(self):
        """Test custom values for EvaluationStats."""
        stats = EvaluationStats(
            total_evaluations=100,
            budget=1000,
            condition="test",
            current_count=100
        )
        assert stats.total_evaluations == 100
        assert stats.budget == 1000
        assert stats.condition == "test"
        assert stats.current_count == 100

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = EvaluationStats(
            total_evaluations=50,
            budget=200,
            condition="mixed",
            current_count=50
        )
        data = stats.to_dict()
        assert data == {
            'total_evaluations': 50,
            'budget': 200,
            'condition': 'mixed',
            'current_count': 50
        }

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'total_evaluations': 75,
            'budget': 300,
            'condition': 'sequential',
            'current_count': 75
        }
        stats = EvaluationStats.from_dict(data)
        assert stats.total_evaluations == 75
        assert stats.budget == 300
        assert stats.condition == 'sequential'
        assert stats.current_count == 75


class TestParityChecker:
    """Tests for the ParityChecker class."""

    def test_initialization(self):
        """Test ParityChecker initialization."""
        checker = ParityChecker(budget=1000, condition="test")
        assert checker.budget == 1000
        assert checker.condition == "test"
        assert checker.current_count == 0
        assert len(checker.history) == 0

    def test_invalid_budget(self):
        """Test that invalid budget raises ValueError."""
        with pytest.raises(ValueError):
            ParityChecker(budget=0, condition="test")

        with pytest.raises(ValueError):
            ParityChecker(budget=-100, condition="test")

    def test_check_and_enforce_success(self):
        """Test successful parity check within budget."""
        checker = ParityChecker(budget=100, condition="test")
        checker.check_and_enforce(increment=10)
        assert checker.current_count == 10
        assert checker.get_remaining() == 90

    def test_check_and_enforce_exactly_at_budget(self):
        """Test check when count equals budget."""
        checker = ParityChecker(budget=100, condition="test")
        checker.current_count = 100
        checker.check_and_enforce(increment=0)
        assert checker.current_count == 100
        assert checker.get_remaining() == 0

    def test_check_and_enforce_exceeds_budget(self):
        """Test that exceeding budget raises ParityError."""
        checker = ParityChecker(budget=100, condition="test")
        checker.current_count = 95
        with pytest.raises(ParityError) as exc_info:
            checker.check_and_enforce(increment=10)

        assert "Parity violation" in str(exc_info.value)
        assert "95" in str(exc_info.value)
        assert "10" in str(exc_info.value)
        assert "100" in str(exc_info.value)
        assert "105" in str(exc_info.value)

    def test_negative_increment(self):
        """Test that negative increment raises ValueError."""
        checker = ParityChecker(budget=100, condition="test")
        with pytest.raises(ValueError):
            checker.check_and_enforce(increment=-1)

    def test_get_remaining(self):
        """Test remaining budget calculation."""
        checker = ParityChecker(budget=1000, condition="test")
        assert checker.get_remaining() == 1000

        checker.check_and_enforce(increment=250)
        assert checker.get_remaining() == 750

        checker.check_and_enforce(increment=500)
        assert checker.get_remaining() == 250

    def test_is_exhausted(self):
        """Test budget exhaustion detection."""
        checker = ParityChecker(budget=100, condition="test")
        assert not checker.is_exhausted()

        checker.check_and_enforce(increment=100)
        assert checker.is_exhausted()

    def test_get_stats(self):
        """Test stats retrieval."""
        checker = ParityChecker(budget=1000, condition="coevolving")
        checker.check_and_enforce(increment=100)

        stats = checker.get_stats()
        assert stats.total_evaluations == 100
        assert stats.budget == 1000
        assert stats.condition == "coevolving"
        assert stats.current_count == 100

    def test_history_tracking(self):
        """Test that history is tracked correctly."""
        checker = ParityChecker(budget=100, condition="test")
        checker.check_and_enforce(increment=10)
        checker.check_and_enforce(increment=20)
        checker.check_and_enforce(increment=30)

        assert len(checker.history) == 3
        assert checker.history[0] == {'count': 10, 'increment': 10, 'remaining': 90}
        assert checker.history[1] == {'count': 30, 'increment': 20, 'remaining': 70}
        assert checker.history[2] == {'count': 60, 'increment': 30, 'remaining': 40}

    def test_save_history(self):
        """Test saving history to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "parity_history.json"
            checker = ParityChecker(budget=100, condition="test")
            checker.check_and_enforce(increment=50)
            checker.save_history(output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data['condition'] == "test"
            assert data['budget'] == 100
            assert data['final_count'] == 50
            assert len(data['history']) == 1


class TestCheckAndEnforceParity:
    """Tests for the standalone check_and_enforce_parity function."""

    def test_within_budget(self):
        """Test function when within budget."""
        result = check_and_enforce_parity(budget=100, current_count=50, condition="test")
        assert result == 50

    def test_exactly_at_budget(self):
        """Test function when exactly at budget."""
        result = check_and_enforce_parity(budget=100, current_count=100, condition="test")
        assert result == 100

    def test_exceeds_budget(self):
        """Test that exceeding budget raises ParityError."""
        with pytest.raises(ParityError) as exc_info:
            check_and_enforce_parity(budget=100, current_count=101, condition="test")

        assert "Parity violation" in str(exc_info.value)
        assert "101" in str(exc_info.value)
        assert "100" in str(exc_info.value)

    def test_default_condition(self):
        """Test default condition name."""
        with pytest.raises(ParityError) as exc_info:
            check_and_enforce_parity(budget=100, current_count=101)

        assert "unknown" in str(exc_info.value)


class TestVerifyRunParity:
    """Tests for the verify_run_parity function."""

    def test_all_conditions_match(self):
        """Test when all conditions match the expected budget."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create history files for each condition
            conditions = ['sequential', 'mixed', 'coevolving']
            for condition in conditions:
                history_file = results_dir / f"parity_history_{condition}.json"
                with open(history_file, 'w') as f:
                    json.dump({
                        'condition': condition,
                        'budget': 1000,
                        'final_count': 1000,
                        'history': []
                    }, f)

            result = verify_run_parity(
                results_dir=results_dir,
                expected_budget=1000,
                conditions=conditions
            )

            for condition in conditions:
                assert result[condition]['verified'] is True
                assert result[condition]['count'] == 1000
                assert result[condition]['budget'] == 1000

    def test_missing_history_file(self):
        """Test when a history file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create only one history file
            history_file = results_dir / "parity_history_sequential.json"
            with open(history_file, 'w') as f:
                json.dump({
                    'condition': 'sequential',
                    'budget': 1000,
                    'final_count': 1000,
                    'history': []
                }, f)

            with pytest.raises(ParityError) as exc_info:
                verify_run_parity(
                    results_dir=results_dir,
                    expected_budget=1000,
                    conditions=['sequential', 'mixed']
                )

            assert "Parity verification failed" in str(exc_info.value)

    def test_count_mismatch(self):
        """Test when count does not match expected budget."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create history file with wrong count
            history_file = results_dir / "parity_history_test.json"
            with open(history_file, 'w') as f:
                json.dump({
                    'condition': 'test',
                    'budget': 1000,
                    'final_count': 950,
                    'history': []
                }, f)

            with pytest.raises(ParityError) as exc_info:
                verify_run_parity(
                    results_dir=results_dir,
                    expected_budget=1000,
                    conditions=['test']
                )

            assert "Parity verification failed" in str(exc_info.value)

    def test_budget_mismatch(self):
        """Test when budget in file does not match expected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create history file with wrong budget
            history_file = results_dir / "parity_history_test.json"
            with open(history_file, 'w') as f:
                json.dump({
                    'condition': 'test',
                    'budget': 900,
                    'final_count': 900,
                    'history': []
                }, f)

            with pytest.raises(ParityError) as exc_info:
                verify_run_parity(
                    results_dir=results_dir,
                    expected_budget=1000,
                    conditions=['test']
                )

            assert "Parity verification failed" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])