"""
Unit tests for utility functions.
"""
import pytest
import numpy as np
from pathlib import Path

# Test imports to ensure modules are loadable
from code.utils.statistical_tests import t_test, anova_one_way, shapiro_test
from code.utils.data_model import Dataset, Transformation, TestResult

def test_shapiro_test_basic():
    """Test that shapiro_test returns expected structure."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    stat, p_value = shapiro_test(data)
    assert isinstance(stat, float)
    assert isinstance(p_value, float)
    assert 0 <= stat <= 1
    assert 0 <= p_value <= 1

def test_data_model_creation():
    """Test that data model classes can be instantiated."""
    dataset = Dataset(
        source_url="http://example.com/data.csv",
        sample_size=100,
        continuous_vars=["var1", "var2"],
        group_labels=["A", "B"],
        shapiro_p=0.03,
        checksum="abc123"
    )
    assert dataset.source_url == "http://example.com/data.csv"
    assert dataset.sample_size == 100

def test_transformation_model_creation():
    """Test that Transformation class can be instantiated."""
    trans = Transformation(
        method="box_cox",
        lambda_param=0.5,
        transformed_values=np.array([1.1, 2.2, 3.3])
    )
    assert trans.method == "box_cox"
    assert trans.lambda_param == 0.5

def test_test_result_model_creation():
    """Test that TestResult class can be instantiated."""
    result = TestResult(
        test_type="t_test",
        p_value=0.04,
        significant=True,
        transformation="box_cox",
        condition="normal",
        effect_size=0.5
    )
    assert result.test_type == "t_test"
    assert result.significant is True