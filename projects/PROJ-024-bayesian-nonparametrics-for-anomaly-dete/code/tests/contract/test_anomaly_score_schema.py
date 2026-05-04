"""Contract test for AnomalyScore dataclass schema."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any

# Import from the correct path per API surface
from models.anomaly_score import AnomalyScore

class TestAnomalyScoreSchema:
    """Verify AnomalyScore dataclass has required fields and types."""

    def test_anomalyscore_has_required_fields(self):
        """AnomalyScore must have timestamp, score, and threshold fields."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        assert hasattr(score, "timestamp")
        assert hasattr(score, "score")
        assert hasattr(score, "threshold")

    def test_anomalyscore_score_is_float(self):
        """AnomalyScore.score must be a float."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        assert isinstance(score.score, float)

    def test_anomalyscore_threshold_is_float(self):
        """AnomalyScore.threshold must be a float."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        assert isinstance(score.threshold, float)

    def test_anomalyscore_is_anomaly_property(self):
        """AnomalyScore must have is_anomaly derived property."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        assert hasattr(score, "is_anomaly")

    def test_anomalyscore_is_anomaly_true(self):
        """AnomalyScore.is_anomaly must be True when score > threshold."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        assert score.is_anomaly is True

    def test_anomalyscore_is_anomaly_false(self):
        """AnomalyScore.is_anomaly must be False when score <= threshold."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.65,
            threshold=0.75
        )
        assert score.is_anomaly is False

    def test_anomalyscore_can_serialize(self):
        """AnomalyScore instances should be serializable to dict."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75
        )
        from dataclasses import asdict
        serialized = asdict(score)
        assert "timestamp" in serialized
        assert "score" in serialized
        assert "threshold" in serialized

    def test_anomalyscore_optional_fields(self):
        """AnomalyScore may have optional fields like confidence."""
        score = AnomalyScore(
            timestamp=datetime(2024, 1, 1),
            score=0.85,
            threshold=0.75,
            confidence=0.9
        )
        assert hasattr(score, "confidence")
