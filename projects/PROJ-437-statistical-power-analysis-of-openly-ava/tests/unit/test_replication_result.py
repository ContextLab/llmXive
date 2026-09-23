"""Unit tests for the ReplicationResult entity.

Validates the structure and basic behavior of the ReplicationResult dataclass.
"""

import pytest
from models.replication_result import ReplicationResult


def test_replication_result_creation():
    """Test that a ReplicationResult can be instantiated with valid data."""
    result = ReplicationResult(
        effect_size_est=0.5,
        p_value=0.03,
        replication_success=True,
        smoothing_kernel_used=4.0
    )
    assert result.effect_size_est == 0.5
    assert result.p_value == 0.03
    assert result.replication_success is True
    assert result.smoothing_kernel_used == 4.0


def test_replication_result_fields_types():
    """Test that fields have the correct types."""
    result = ReplicationResult(
        effect_size_est=1.2,
        p_value=0.001,
        replication_success=False,
        smoothing_kernel_used=8.0
    )
    assert isinstance(result.effect_size_est, float)
    assert isinstance(result.p_value, float)
    assert isinstance(result.replication_success, bool)
    assert isinstance(result.smoothing_kernel_used, float)


def test_replication_result_edge_cases():
    """Test edge cases like zero p-value and zero effect size."""
    result = ReplicationResult(
        effect_size_est=0.0,
        p_value=1.0,
        replication_success=False,
        smoothing_kernel_used=0.0
    )
    assert result.effect_size_est == 0.0
    assert result.p_value == 1.0
    assert result.replication_success is False
    assert result.smoothing_kernel_used == 0.0