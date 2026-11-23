"""
Unit tests for data_validator.py (T010).
Tests the validate_data_completeness function logic.
"""
import pytest
from code.analysis.data_validator import validate_data_completeness, get_missing_variables, CRITICAL_VARS, NON_CRITICAL_VARS

class TestDataValidator:
    """Test suite for data completeness validation."""

    def test_empty_run_data(self):
        """Test that empty run data is rejected."""
        result, reason = validate_data_completeness([])
        assert result is False
        assert "empty" in reason.lower()

    def test_missing_critical_throughput(self):
        """Test run exclusion when throughput_ops is missing."""
        run_data = [
            {"latency_ms": 50.0, "cpu_utilization_pct": 75.0},
            {"latency_ms": 55.0, "cpu_utilization_pct": 80.0}
        ]
        result, reason = validate_data_completeness(run_data)
        assert result is False
        assert "throughput_ops" in reason
        assert "excluded" in reason.lower()

    def test_missing_critical_latency(self):
        """Test run exclusion when latency_ms is missing."""
        run_data = [
            {"throughput_ops": 1000.0, "cpu_utilization_pct": 75.0},
            {"throughput_ops": 1100.0, "cpu_utilization_pct": 80.0}
        ]
        result, reason = validate_data_completeness(run_data)
        assert result is False
        assert "latency_ms" in reason
        assert "excluded" in reason.lower()

    def test_missing_both_critical(self):
        """Test run exclusion when both critical variables are missing."""
        run_data = [
            {"cpu_utilization_pct": 75.0},
            {"cpu_utilization_pct": 80.0}
        ]
        result, reason = validate_data_completeness(run_data)
        assert result is False
        assert "throughput_ops" in reason
        assert "latency_ms" in reason
        assert "excluded" in reason.lower()

    def test_critical_present_non_critical_missing(self):
        """Test run acceptance with reduced model when non-critical vars missing."""
        run_data = [
            {"throughput_ops": 1000.0, "latency_ms": 50.0},
            {"throughput_ops": 1100.0, "latency_ms": 55.0}
        ]
        result, reason = validate_data_completeness(run_data)
        assert result is True
        assert "reduced model" in reason.lower()
        assert "passed" not in reason.lower()  # Not a full pass

    def test_all_variables_present(self):
        """Test full pass when all variables are present."""
        run_data = [
            {
                "throughput_ops": 1000.0,
                "latency_ms": 50.0,
                "cpu_utilization_pct": 75.0,
                "packet_loss_rate": 0.01,
                "node_heterogeneity_score": 0.5
            },
            {
                "throughput_ops": 1100.0,
                "latency_ms": 55.0,
                "cpu_utilization_pct": 80.0,
                "packet_loss_rate": 0.02,
                "node_heterogeneity_score": 0.6
            }
        ]
        result, reason = validate_data_completeness(run_data)
        assert result is True
        assert "passed" in reason.lower()
        assert "reduced model" not in reason.lower()

    def test_mixed_records_some_missing_critical(self):
        """Test that if ANY record has critical vars, the run is not excluded for that reason."""
        # First record has critical vars, second doesn't
        run_data = [
            {"throughput_ops": 1000.0, "latency_ms": 50.0},
            {"cpu_utilization_pct": 75.0}  # Missing critical
        ]
        # Should pass because at least one record has critical vars
        result, reason = validate_data_completeness(run_data)
        assert result is True

    def test_none_values_for_critical(self):
        """Test that None values for critical variables count as missing."""
        run_data = [
            {"throughput_ops": None, "latency_ms": 50.0},
            {"throughput_ops": 1000.0, "latency_ms": None}
        ]
        result, reason = validate_data_completeness(run_data)
        # First record has no valid throughput, second has no valid latency
        # But first has latency, second has throughput -> both present overall
        assert result is True

    def test_get_missing_variables_empty(self):
        """Test get_missing_variables with empty data."""
        missing_crit, missing_non_crit = get_missing_variables([])
        assert missing_crit == set()
        assert missing_non_crit == set()

    def test_get_missing_variables_full(self):
        """Test get_missing_variables with all variables present."""
        run_data = [
            {
                "throughput_ops": 1000.0,
                "latency_ms": 50.0,
                "cpu_utilization_pct": 75.0,
                "packet_loss_rate": 0.01,
                "node_heterogeneity_score": 0.5
            }
        ]
        missing_crit, missing_non_crit = get_missing_variables(run_data)
        assert missing_crit == set()
        assert missing_non_crit == set()

    def test_get_missing_variables_partial(self):
        """Test get_missing_variables with some variables missing."""
        run_data = [
            {
                "throughput_ops": 1000.0,
                "latency_ms": 50.0
                # Missing all non-critical
            }
        ]
        missing_crit, missing_non_crit = get_missing_variables(run_data)
        assert missing_crit == set()
        assert missing_non_crit == NON_CRITICAL_VARS

    def test_get_missing_variables_critical_missing(self):
        """Test get_missing_variables with critical variables missing."""
        run_data = [
            {
                "cpu_utilization_pct": 75.0,
                "packet_loss_rate": 0.01
                # Missing throughput and latency
            }
        ]
        missing_crit, missing_non_crit = get_missing_variables(run_data)
        assert missing_crit == CRITICAL_VARS
        assert missing_non_crit == set()