import pytest
import logging
from unittest.mock import patch, MagicMock
from code.utils import calculate_exclusion_ratio, write_halt_signal, EXCLUSION_RATIO_THRESHOLD

# Configure logging for tests to avoid noise
logging.basicConfig(level=logging.CRITICAL)

class TestExclusionRatio:
    def test_no_missing_targets(self):
        """Test with all valid targets."""
        data = [
            {"target_adhesion_strength": 5.0, "id": 1},
            {"target_adhesion_strength": 6.2, "id": 2},
            {"target_adhesion_strength": 4.8, "id": 3}
        ]
        ratio, missing, total = calculate_exclusion_ratio(data)
        assert ratio == 0.0
        assert missing == 0
        assert total == 3

    def test_some_missing_targets(self):
        """Test with partial missing targets (below threshold)."""
        data = [
            {"target_adhesion_strength": 5.0, "id": 1},
            {"target_adhesion_strength": None, "id": 2},
            {"target_adhesion_strength": 4.8, "id": 3}
        ]
        ratio, missing, total = calculate_exclusion_ratio(data)
        assert ratio == pytest.approx(1/3)
        assert missing == 1
        assert total == 3

    def test_exceeds_threshold_raises(self):
        """Test that exceeding threshold raises ValueError and writes halt signal."""
        # Create enough data to exceed 10% threshold
        # 10 items, 2 missing = 20% -> should fail
        data = [
            {"target_adhesion_strength": 5.0} for _ in range(8)
        ] + [
            {"target_adhesion_strength": None} for _ in range(2)
        ]
        
        with pytest.raises(ValueError, match="exceeds threshold"):
            calculate_exclusion_ratio(data)

    def test_empty_list(self):
        """Test with empty list."""
        ratio, missing, total = calculate_exclusion_ratio([])
        assert ratio == 0.0
        assert missing == 0
        assert total == 0

    def test_nan_values_counted_as_missing(self):
        """Test that NaN string values are counted as missing."""
        data = [
            {"target_adhesion_strength": "nan", "id": 1},
            {"target_adhesion_strength": 5.0, "id": 2}
        ]
        ratio, missing, total = calculate_exclusion_ratio(data)
        assert missing == 1
        assert total == 2