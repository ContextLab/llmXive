"""
Tests for entropy.py
"""
import pytest
import os
import json
import tempfile
import csv
from pathlib import Path
from src.entropy import (
    normalize_ast,
    cluster_by_semantic_equivalence,
    compute_shannon_entropy,
    write_entropy_results,
    log_exclusions,
    process_entropy_for_dataset
)

def test_normalize_ast_valid():
    code = "def foo(): return 1"
    result = normalize_ast(code)
    assert result is not None
    assert "def foo" in result.lower()

def test_normalize_ast_invalid():
    code = "def foo(: return 1" # Invalid syntax
    result = normalize_ast(code)
    assert result is None

def test_cluster_by_semantic_equivalence_ast():
    samples = [
        "def foo(): return 1",
        "def foo():\n    return 1", # Same AST, different whitespace
        "def bar(): return 2"
    ]
    clusters = cluster_by_semantic_equivalence(samples)
    # First two should be in same cluster, third in different
    assert clusters[0] == clusters[1]
    assert clusters[0] != clusters[2]

def test_compute_shannon_entropy():
    # 2 clusters, sizes 2 and 2 -> p=0.5, H = 1.0
    cluster_map = {0: 0, 1: 0, 2: 1, 3: 1}
    entropy = compute_shannon_entropy(cluster_map)
    assert abs(entropy - 1.0) < 0.01

def test_write_entropy_results(tmp_path):
    results = [
        {"task_id": "t1", "entropy": 1.0, "cluster_count": 2, "excluded_reason": ""},
        {"task_id": "t2", "entropy": 0.0, "cluster_count": 1, "excluded_reason": "No samples"}
    ]
    output_path = tmp_path / "entropy_results.csv"
    write_entropy_results(results, str(output_path))

    assert output_path.exists()
    exclusion_log_path = tmp_path / "exclusion_log.json"
    assert exclusion_log_path.exists()

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['task_id'] == 't1'
        assert rows[1]['excluded_reason'] == 'No samples'

    with open(exclusion_log_path, 'r') as f:
        log_data = json.load(f)
        assert log_data['excluded_count'] == 1
        assert log_data['exclusion_rate'] == 0.5

def test_process_entropy_for_dataset():
    samples = ["x=1", "x=1", "y=2"]
    result = process_entropy_for_dataset("test_task", samples)
    assert result['task_id'] == 'test_task'
    assert result['entropy'] >= 0
    assert result['cluster_count'] >= 1
    assert result['excluded_reason'] == ""

class TestEntropyClusteringLogic:
    def test_cluster_samples_exact_match(self):
        samples = ["a", "a", "b"]
        clusters = cluster_by_semantic_equivalence(samples)
        assert clusters[0] == clusters[1]
        assert clusters[0] != clusters[2]

    def test_cluster_samples_ast_normalized(self):
        samples = [
            "def f(): return 1",
            "def f():\n    return 1"
        ]
        clusters = cluster_by_semantic_equivalence(samples)
        assert clusters[0] == clusters[1]

    def test_cluster_samples_execution(self):
        # This would require a working sandbox. For now, we test the fallback logic.
        # If AST fails, it tries execution.
        samples = ["invalid", "invalid2"] # Both fail AST
        clusters = cluster_by_semantic_equivalence(samples)
        # They might be in different clusters if execution output differs, or same if same error
        # We just check it doesn't crash and returns a dict
        assert isinstance(clusters, dict)
        assert len(clusters) == 2

    def test_compute_shannon_entropy_zero(self):
        # All in one cluster -> p=1, H=0
        cluster_map = {0: 0, 1: 0, 2: 0}
        entropy = compute_shannon_entropy(cluster_map)
        assert entropy == 0.0

    def test_calculate_semantic_entropy(self):
        # Wrapper test
        samples = ["x=1", "y=2"]
        result = process_entropy_for_dataset("t", samples)
        assert 'entropy' in result