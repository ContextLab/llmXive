"""
Unit tests for T021d: run_matching_report.py
"""
import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.run_matching_report import (
    calculate_baseline_stats,
    evaluate_matching_quality
)

@pytest.fixture
def sample_baseline():
    return {
        "repos": [
            {"repo_id": "b1", "loc": 5000, "cc": 120},
            {"repo_id": "b2", "loc": 5000, "cc": 120},
            {"repo_id": "b3", "loc": 5000, "cc": 120}
        ]
    }

@pytest.fixture
def sample_candidates():
    return {
        "repos": [
            {"repo_id": "c1", "loc": 5000, "cc": 120},  # Perfect match
            {"repo_id": "c2", "loc": 5200, "cc": 122},  # Within 15%
            {"repo_id": "c3", "loc": 10000, "cc": 200}, # Outlier (LOC > 15%)
            {"repo_id": "c4", "loc": 4800, "cc": 118}   # Within 15%
        ]
    }

def test_calculate_baseline_stats(sample_baseline):
    stats = calculate_baseline_stats(sample_baseline)
    assert stats["mean_loc"] == 5000.0
    assert stats["mean_cc"] == 120.0

def test_evaluate_matching_quality_accepts_within_tolerance(sample_baseline, sample_candidates):
    baseline_stats = calculate_baseline_stats(sample_baseline)
    results = evaluate_matching_quality(sample_candidates, baseline_stats)
    
    # c1, c2, c4 should be accepted (within 15%)
    # c3 should be excluded (LOC is 10000, 100% deviation)
    assert results["total_accepted"] == 3
    assert results["total_excluded"] == 1
    
    accepted_ids = [r["repo_id"] for r in results["accepted_repos"]]
    assert "c1" in accepted_ids
    assert "c2" in accepted_ids
    assert "c4" in accepted_ids
    
    excluded_ids = [r["repo_id"] for r in results["excluded_repos"]]
    assert "c3" in excluded_ids
    assert "LOC deviation" in results["excluded_repos"][0]["reasons"][0]

def test_evaluate_matching_quality_handles_missing_metrics(sample_baseline):
    candidates = {
        "repos": [
            {"repo_id": "bad", "loc": None, "cc": 100}
        ]
    }
    baseline_stats = calculate_baseline_stats(sample_baseline)
    results = evaluate_matching_quality(candidates, baseline_stats)
    
    assert results["total_accepted"] == 0
    assert results["total_excluded"] == 1
    assert results["excluded_repos"][0]["reason"] == "Missing LOC or CC metrics"