import pytest
import numpy as np
import logging
from code.logging_config import (
    E_NUMERICAL_INSTABILITY,
    E_DATA_EXCLUSION,
    check_numerical_stability,
    log_data_exclusion,
    get_instability_events,
    get_exclusion_events,
    clear_event_logs,
    logger
)

class TestNumericalStability:
    """Tests for numerical stability checking functionality."""

    def setup_method(self):
        """Clear event logs before each test."""
        clear_event_logs()

    def test_stable_data_passes(self):
        """Test that stable data passes the check."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = check_numerical_stability(data, "test_stable")
        assert result is True
        assert len(get_instability_events()) == 0

    def test_nan_data_raises_exception(self):
        """Test that NaN values raise E_NUMERICAL_INSTABILITY."""
        data = np.array([1.0, np.nan, 3.0, 4.0])
        with pytest.raises(E_NUMERICAL_INSTABILITY) as exc_info:
            check_numerical_stability(data, "test_nan")
        
        assert "NaN" in str(exc_info.value)
        events = get_instability_events()
        assert len(events) == 1
        assert events[0]['has_nan'] is True
        assert events[0]['nan_count'] == 1

    def test_inf_data_raises_exception(self):
        """Test that Inf values raise E_NUMERICAL_INSTABILITY."""
        data = np.array([1.0, 2.0, np.inf, 4.0])
        with pytest.raises(E_NUMERICAL_INSTABILITY) as exc_info:
            check_numerical_stability(data, "test_inf")
        
        assert "Inf" in str(exc_info.value)
        events = get_instability_events()
        assert len(events) == 1
        assert events[0]['has_inf'] is True
        assert events[0]['inf_count'] == 1

    def test_nan_and_inf_data_raises_exception(self):
        """Test that both NaN and Inf values are detected."""
        data = np.array([1.0, np.nan, np.inf, 4.0])
        with pytest.raises(E_NUMERICAL_INSTABILITY):
            check_numerical_stability(data, "test_both")
        
        events = get_instability_events()
        assert len(events) == 1
        assert events[0]['has_nan'] is True
        assert events[0]['has_inf'] is True
        assert events[0]['nan_count'] == 1
        assert events[0]['inf_count'] == 1

    def test_multidimensional_array_check(self):
        """Test stability check on multi-dimensional arrays."""
        data = np.array([[1.0, 2.0], [3.0, np.nan]])
        with pytest.raises(E_NUMERICAL_INSTABILITY):
            check_numerical_stability(data, "test_2d")

        events = get_instability_events()
        assert len(events) == 1
        assert events[0]['shape'] == (2, 2)

    def test_list_conversion(self):
        """Test that lists are converted to numpy arrays."""
        data = [1.0, 2.0, 3.0]
        result = check_numerical_stability(data, "test_list")
        assert result is True

    def test_list_with_nan(self):
        """Test that lists with NaN are detected."""
        data = [1.0, float('nan'), 3.0]
        with pytest.raises(E_NUMERICAL_INSTABILITY):
            check_numerical_stability(data, "test_list_nan")

class TestDataExclusionLogging:
    """Tests for data exclusion logging functionality."""

    def setup_method(self):
        """Clear event logs before each test."""
        clear_event_logs()

    def test_log_exclusion_with_count(self):
        """Test logging exclusion with count."""
        log_data_exclusion(
            reason="Failed validation",
            context="test_context",
            affected_count=5
        )
        
        events = get_exclusion_events()
        assert len(events) == 1
        assert events[0]['reason'] == "Failed validation"
        assert events[0]['context'] == "test_context"
        assert events[0]['affected_count'] == 5

    def test_log_exclusion_with_indices(self):
        """Test logging exclusion with specific indices."""
        log_data_exclusion(
            reason="NaN detected",
            context="metric_calculation",
            affected_indices=[1, 5, 10],
            affected_count=3
        )
        
        events = get_exclusion_events()
        assert len(events) == 1
        assert events[0]['affected_indices'] == [1, 5, 10]
        assert events[0]['affected_count'] == 3

    def test_log_exclusion_minimal(self):
        """Test logging exclusion with minimal parameters."""
        log_data_exclusion(reason="Invalid data", context="minimal_test")
        
        events = get_exclusion_events()
        assert len(events) == 1
        assert events[0]['reason'] == "Invalid data"
        assert events[0]['context'] == "minimal_test"

class TestEventLogManagement:
    """Tests for event log management functions."""

    def setup_method(self):
        """Clear event logs before each test."""
        clear_event_logs()

    def test_clear_instability_events(self):
        """Test clearing instability events."""
        # Add an event
        try:
            check_numerical_stability(np.array([np.nan]), "test")
        except E_NUMERICAL_INSTABILITY:
            pass
        
        assert len(get_instability_events()) == 1
        clear_event_logs()
        assert len(get_instability_events()) == 0

    def test_clear_exclusion_events(self):
        """Test clearing exclusion events."""
        log_data_exclusion("Test reason", "test_context", affected_count=1)
        assert len(get_exclusion_events()) == 1
        clear_event_logs()
        assert len(get_exclusion_events()) == 0

    def test_events_are_copies(self):
        """Test that get functions return copies, not references."""
        log_data_exclusion("Test", "ctx", affected_count=1)
        events = get_exclusion_events()
        events.append({"fake": "event"})
        
        # Original should be unchanged
        assert len(get_exclusion_events()) == 1

class TestLoggerSetup:
    """Tests for logger setup functionality."""

    def test_logger_exists(self):
        """Test that the global logger is created."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_logger_level(self):
        """Test that logger level is set correctly."""
        assert logger.level == logging.INFO

    def test_logger_has_handler(self):
        """Test that logger has at least one handler."""
        assert len(logger.handlers) > 0