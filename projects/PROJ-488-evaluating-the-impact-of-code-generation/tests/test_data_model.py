import pytest
import math
from code.data_model import MetricResult, validate_metric_result

def test_validate_metric_result_valid():
    """Test that a valid MetricResult passes validation."""
    result = MetricResult(
        metric_type="cyclomatic_complexity",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )
    assert validate_metric_result(result) is True

def test_validate_metric_result_missing_type():
    """Test that missing metric_type fails validation."""
    result = MetricResult(
        metric_type="",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )
    assert validate_metric_result(result) is False

def test_validate_metric_result_negative_variance():
    """Test that negative variance fails validation."""
    result = MetricResult(
        metric_type="test",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=-1.0,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )
    assert validate_metric_result(result) is False

def test_validate_metric_result_min_gt_max():
    """Test that min_val > max_val fails validation."""
    result = MetricResult(
        metric_type="test",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=10.0,
        max_val=1.0,
        count=100
    )
    assert validate_metric_result(result) is False

def test_validate_metric_result_mean_out_of_bounds():
    """Test that mean outside [min, max] fails validation."""
    result = MetricResult(
        metric_type="test",
        group_label="human",
        mean=15.0,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )
    assert validate_metric_result(result) is False

def test_validate_metric_result_nan():
    """Test that NaN values fail validation."""
    result = MetricResult(
        metric_type="test",
        group_label="human",
        mean=float('nan'),
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=100
    )
    assert validate_metric_result(result) is False

def test_validate_metric_result_count_negative():
    """Test that negative count fails validation."""
    result = MetricResult(
        metric_type="test",
        group_label="human",
        mean=5.5,
        median=5.0,
        variance=2.25,
        std_dev=1.5,
        min_val=1.0,
        max_val=10.0,
        count=-1
    )
    assert validate_metric_result(result) is False
