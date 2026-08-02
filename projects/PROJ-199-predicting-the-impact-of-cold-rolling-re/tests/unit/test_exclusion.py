"""
Unit tests for the exclusion logic in code/data/exclusion.py
"""
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import os

# Import the functions to test
from data.exclusion import calculate_reliability_metrics, apply_exclusion_logic

def test_calculate_reliability_metrics_all_reliable():
    """Test that samples with 0% filtered points are marked reliable."""
    data = {
        "sample_id": ["s1", "s1", "s2", "s2"],
        "confidence_index": [0.9, 0.8, 0.95, 0.99]
    }
    df = pd.DataFrame(data)
    metrics = calculate_reliability_metrics(df)

    assert len(metrics) == 2
    assert all(metrics["is_reliable"] == True)
    assert all(metrics["filtered_points"] == 0)
    assert all(metrics["reliability_ratio"] == 1.0)

def test_calculate_reliability_metrics_all_unreliable():
    """Test that samples with >50% filtered points are marked unreliable."""
    data = {
        "sample_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
        "confidence_index": [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    metrics = calculate_reliability_metrics(df)

    assert len(metrics) == 2
    assert all(metrics["is_reliable"] == False)
    assert all(metrics["filtered_points"] == 3)
    assert all(metrics["reliability_ratio"] == 0.0)

def test_calculate_reliability_metrics_boundary_case():
    """Test the boundary case where exactly 50% are filtered."""
    data = {
        "sample_id": ["s1", "s1", "s2", "s2", "s2", "s2"],
        "confidence_index": [0.05, 0.9, 0.05, 0.05, 0.9, 0.9]
    }
    df = pd.DataFrame(data)
    metrics = calculate_reliability_metrics(df)

    # s1: 1 filtered out of 2 -> 50% filtered -> reliability 0.5 -> is_reliable = True (>= 0.5)
    # s2: 2 filtered out of 4 -> 50% filtered -> reliability 0.5 -> is_reliable = True
    s1_row = metrics[metrics["sample_id"] == "s1"].iloc[0]
    s2_row = metrics[metrics["sample_id"] == "s2"].iloc[0]

    assert s1_row["is_reliable"] == True
    assert s2_row["is_reliable"] == True
    assert s1_row["reliability_ratio"] == 0.5

def test_apply_exclusion_logic():
    """Test that apply_exclusion_logic correctly removes unreliable samples."""
    data = {
        "sample_id": ["s1", "s1", "s2", "s2", "s2", "s2"],
        "value": [1, 2, 3, 4, 5, 6],
        "confidence_index": [0.9, 0.8, 0.05, 0.05, 0.9, 0.9]
    }
    df = pd.DataFrame(data)

    # s1: 0 filtered -> reliable
    # s2: 2 filtered out of 4 -> 50% -> reliable
    # Let's make s3 unreliable: 3 out of 4 filtered
    data["sample_id"].extend(["s3", "s3", "s3", "s3"])
    data["value"].extend([7, 8, 9, 10])
    data["confidence_index"].extend([0.05, 0.05, 0.05, 0.9]) # 3/4 filtered

    df = pd.DataFrame(data)
    metrics = calculate_reliability_metrics(df)

    filtered_df = apply_exclusion_logic(df, metrics)

    # s3 should be excluded
    assert "s3" not in filtered_df["sample_id"].values
    assert "s1" in filtered_df["sample_id"].values
    assert "s2" in filtered_df["sample_id"].values
    assert len(filtered_df) == 6 # s1(2) + s2(4)

def test_apply_exclusion_logic_empty_input():
    """Test behavior with empty DataFrame."""
    df = pd.DataFrame(columns=["sample_id", "confidence_index"])
    metrics = pd.DataFrame(columns=["sample_id", "is_reliable"])

    result = apply_exclusion_logic(df, metrics)
    assert result.empty

def test_apply_exclusion_logic_no_unreliable():
    """Test when no samples are excluded."""
    data = {
        "sample_id": ["s1", "s1"],
        "value": [1, 2],
        "confidence_index": [0.9, 0.9]
    }
    df = pd.DataFrame(data)
    metrics = calculate_reliability_metrics(df)

    filtered_df = apply_exclusion_logic(df, metrics)
    assert len(filtered_df) == 2
    assert list(filtered_df["sample_id"]) == ["s1", "s1"]

def test_missing_confidence_column():
    """Test that ValueError is raised if confidence column is missing."""
    data = {
        "sample_id": ["s1"],
        "value": [1]
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError, match="Column 'confidence_index' not found"):
        calculate_reliability_metrics(df)