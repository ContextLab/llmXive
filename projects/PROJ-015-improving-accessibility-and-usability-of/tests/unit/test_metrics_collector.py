import time
import pytest
from code.simulator.metrics_collector import MetricsCollector

class TestMetricsCollector:
    def test_initialization(self):
        collector = MetricsCollector()
        assert collector.error_count == 0
        assert collector.explanation_engagement_total == 0.0
        assert collector.session_start_time is None

    def test_completion_time_calculation(self):
        collector = MetricsCollector()
        collector.start_session()
        time.sleep(0.05)  # Small delay to ensure non-zero time
        collector.stop_session()
        
        metrics = collector.finalize_metrics()
        assert metrics["completion_time_seconds"] >= 0.05
        assert "error_count" in metrics

    def test_error_counting(self):
        collector = MetricsCollector()
        collector.start_session()
        collector.record_error()
        collector.record_error()
        collector.stop_session()
        
        metrics = collector.finalize_metrics()
        assert metrics["error_count"] == 2

    def test_explanation_engagement_time_seconds(self):
        """
        T016b Verification: Ensure explanation_engagement_time_seconds is 
        calculated and included in the final metrics dictionary.
        """
        collector = MetricsCollector()
        collector.start_session()
        
        # Start engagement
        collector.start_explanation_engagement()
        time.sleep(0.1)
        collector.stop_explanation_engagement()
        
        collector.stop_session()
        
        metrics = collector.finalize_metrics()
        
        # Verify the field exists and is a number
        assert "explanation_engagement_time_seconds" in metrics, \
            "explanation_engagement_time_seconds must be present in metrics"
        assert isinstance(metrics["explanation_engagement_time_seconds"], (int, float)), \
            "explanation_engagement_time_seconds must be numeric"
        assert metrics["explanation_engagement_time_seconds"] >= 0.1, \
            "explanation_engagement_time_seconds should reflect the elapsed time"

    def test_multiple_engagement_periods(self):
        collector = MetricsCollector()
        collector.start_session()
        
        collector.start_explanation_engagement()
        time.sleep(0.1)
        collector.stop_explanation_engagement()
        
        collector.start_explanation_engagement()
        time.sleep(0.1)
        collector.stop_explanation_engagement()
        
        collector.stop_session()
        
        metrics = collector.finalize_metrics()
        assert metrics["explanation_engagement_time_seconds"] >= 0.2

    def test_session_must_be_complete(self):
        collector = MetricsCollector()
        collector.start_session()
        # Missing stop_session
        with pytest.raises(RuntimeError):
            collector.finalize_metrics()
