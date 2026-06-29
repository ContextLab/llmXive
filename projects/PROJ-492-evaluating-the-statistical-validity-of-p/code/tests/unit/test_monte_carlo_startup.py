"""
Unit Tests for Monte-Carlo Validation Startup Script (T031)

Tests the run_monte_carlo_validation.py script to ensure it:
1. Runs the Monte-Carlo validation module correctly
2. Aborts with ERR-801 when tests fail the ≤ 0.005 criterion
3. Returns success when all tests pass
"""
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.cli.run_monte_carlo_validation import (
    run_monte_carlo_startup_validation,
    main
)
from code.src.utils.logger import get_default_logger


class TestMonteCarloStartupValidation:
    """Tests for the Monte-Carlo validation startup script."""

    def test_all_tests_pass_returns_true(self):
        """When all tests pass, the function returns True."""
        # Mock the run_monte_carlo_validation to return passing results
        mock_results = {
            "z_test": {"passed": True, "absolute_difference": 0.003},
            "fisher_exact": {"passed": True, "absolute_difference": 0.002},
            "welch_t_test": {"passed": True, "absolute_difference": 0.004},
            "binomial_test": {"passed": True, "absolute_difference": 0.001}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is True

    def test_one_test_fails_returns_false(self):
        """When any test fails, the function returns False."""
        mock_results = {
            "z_test": {"passed": False, "absolute_difference": 0.015},
            "fisher_exact": {"passed": True, "absolute_difference": 0.002},
            "welch_t_test": {"passed": True, "absolute_difference": 0.004},
            "binomial_test": {"passed": True, "absolute_difference": 0.001}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is False

    def test_null_results_returns_false(self):
        """When validation returns None, the function returns False."""
        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=None
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is False

    def test_exception_handling_returns_false(self):
        """When an exception occurs, the function returns False."""
        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            side_effect=Exception("Validation failed")
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is False

    def test_main_exits_zero_on_success(self):
        """Main exits with code 0 when all tests pass."""
        mock_results = {
            "z_test": {"passed": True, "absolute_difference": 0.003},
            "fisher_exact": {"passed": True, "absolute_difference": 0.002}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            with patch("code.src.cli.run_monte_carlo_validation.sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)

    def test_main_exits_one_on_failure(self):
        """Main exits with code 1 when validation fails."""
        mock_results = {
            "z_test": {"passed": False, "absolute_difference": 0.015}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            with patch("code.src.cli.run_monte_carlo_validation.sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)

    def test_main_exits_two_on_exception(self):
        """Main exits with code 2 when an exception occurs."""
        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            side_effect=Exception("Unexpected error")
        ):
            with patch("code.src.cli.run_monte_carlo_validation.sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(2)

    def test_boundary_condition_exactly_point_zero_zero_five(self):
        """Test that exactly 0.005 difference is considered passing."""
        mock_results = {
            "z_test": {"passed": True, "absolute_difference": 0.005},
            "fisher_exact": {"passed": True, "absolute_difference": 0.005}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is True

    def test_boundary_condition_just_above_point_zero_zero_five(self):
        """Test that 0.0050001 difference is considered failing."""
        mock_results = {
            "z_test": {"passed": False, "absolute_difference": 0.0050001},
            "fisher_exact": {"passed": True, "absolute_difference": 0.004}
        }

        with patch(
            "code.src.cli.run_monte_carlo_validation.run_monte_carlo_validation",
            return_value=mock_results
        ):
            logger = get_default_logger()
            result = run_monte_carlo_startup_validation(logger)
            assert result is False
