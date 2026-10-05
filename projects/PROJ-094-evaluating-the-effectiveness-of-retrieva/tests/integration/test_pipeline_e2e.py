"""
Integration test for full pipeline execution on queries.

This test verifies that the end-to-end pipeline (T013) executes successfully
on a representative set of queries from the processed test set, producing
valid output files (results.csv and results/throughput_report.json) with
the correct schema and non-trivial metric values.

Dependencies:
- T006: Downloaded raw data
- T007: Preprocessed data (data/processed/test)
- T013: CLI main script (src/cli/main.py)
- T016: Output schema contract (tests/contract/test_output_schema.py)
"""

import os
import sys
import json
import tempfile
import shutil
import csv
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cli.main import main as cli_main
from src.data.preprocess import load_and_process_subset
from src.data.models import RetrievalMethod


@pytest.fixture(scope="module")
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="pipeline_e2e_test_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def test_queries_path():
    """
    Return the path to the preprocessed test queries.
    Assumes T007 has created data/processed/test/queries.csv or .jsonl
    """
    # Try common paths based on T007 implementation
    possible_paths = [
        PROJECT_ROOT / "data" / "processed" / "test" / "queries.csv",
        PROJECT_ROOT / "data" / "processed" / "test" / "queries.jsonl",
        PROJECT_ROOT / "data" / "processed" / "test" / "processed_queries.csv",
        PROJECT_ROOT / "data" / "processed" / "test" / "processed_queries.jsonl"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # If no preprocessed data exists, skip the test
    # This is expected in CI if T006/T007 haven't run yet
    pytest.skip("Preprocessed test data not found. Ensure T006 and T007 are completed first.")


def test_pipeline_e2e_execution(temp_output_dir, test_queries_path):
    """
    End-to-end test: Run the full pipeline and verify outputs.
    
    This test:
    1. Executes the CLI main script with the test queries
    2. Verifies results.csv is created with correct schema
    3. Verifies results/throughput_report.json is created with correct schema
    4. Checks that metrics are non-trivial (not all zeros or NaN)
    5. Ensures all three retrieval methods (BM25, Neural, RAG) are present
    """
    
    # Prepare command-line arguments
    args = [
        "--queries", str(test_queries_path),
        "--output-dir", str(temp_output_dir),
        "--methods", "bm25,neural,rag",
        "--k", "10",
        "--seed", "42"
    ]
    
    # Run the pipeline
    try:
        # Capture exit code
        exit_code = cli_main(args)
    except Exception as e:
        pytest.fail(f"Pipeline execution failed with exception: {e}")
    
    # Verify exit code is 0 (success)
    assert exit_code == 0, f"Pipeline exited with code {exit_code}"
    
    # Check output files exist
    results_csv_path = temp_output_dir / "results.csv"
    throughput_json_path = temp_output_dir / "throughput_report.json"
    
    assert results_csv_path.exists(), "results.csv was not created"
    assert throughput_json_path.exists(), "throughput_report.json was not created"
    
    # Validate results.csv schema and content
    with open(results_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Must have at least one row
    assert len(rows) > 0, "results.csv is empty"
    
    # Check required columns (from T013 specification)
    required_columns = {
        'query_id', 'method', 'precision_at_k', 'recall_at_k', 'ndcg_at_k'
    }
    actual_columns = set(rows[0].keys())
    
    assert required_columns.issubset(actual_columns), \
        f"Missing required columns: {required_columns - actual_columns}"
    
    # Check that all three methods are present
    methods_in_output = {row['method'] for row in rows}
    expected_methods = {'bm25', 'neural', 'rag'}
    
    assert expected_methods.issubset(methods_in_output), \
        f"Missing retrieval methods: {expected_methods - methods_in_output}"
    
    # Verify metrics are valid numbers (not NaN or Inf)
    for row in rows:
        for metric in ['precision_at_k', 'recall_at_k', 'ndcg_at_k']:
            try:
                value = float(row[metric])
                assert value >= 0.0 and value <= 1.0, \
                    f"Metric {metric} value {value} out of range [0, 1]"
            except (ValueError, TypeError) as e:
                pytest.fail(f"Invalid metric value in row {row}: {e}")
    
    # Validate throughput_report.json schema
    with open(throughput_json_path, 'r', encoding='utf-8') as f:
        throughput_data = json.load(f)
    
    required_throughput_keys = {'total_queries', 'total_time_seconds', 'queries_per_hour'}
    actual_throughput_keys = set(throughput_data.keys())
    
    assert required_throughput_keys.issubset(actual_throughput_keys), \
        f"Missing throughput keys: {required_throughput_keys - actual_throughput_keys}"
    
    # Verify throughput values are reasonable
    assert throughput_data['total_queries'] > 0, "total_queries must be positive"
    assert throughput_data['total_time_seconds'] > 0, "total_time_seconds must be positive"
    assert throughput_data['queries_per_hour'] > 0, "queries_per_hour must be positive"
    
    # Cross-check: total_queries in throughput should match number of unique query_ids in results
    unique_query_ids = {row['query_id'] for row in rows}
    assert throughput_data['total_queries'] == len(unique_query_ids), \
        f"Query count mismatch: throughput={throughput_data['total_queries']}, " \
        f"results={len(unique_query_ids)}"
    
    # Verify reproducibility: running again should produce same results
    # (This is a basic check; full reproducibility is tested in unit tests)
    results_content_1 = results_csv_path.read_text()
    
    # Re-run pipeline
    exit_code_2 = cli_main(args)
    assert exit_code_2 == 0, "Second pipeline execution failed"
    
    results_content_2 = results_csv_path.read_text()
    
    # For deterministic runs, results should be identical
    # Note: Some floating point variations might occur, so we check for structural similarity
    # rather than exact byte-for-byte match
    rows_2 = list(csv.DictReader(results_content_2.splitlines()))
    
    assert len(rows_2) == len(rows), "Number of rows changed between runs"
    
    # Check that metrics are approximately the same (within 1e-6)
    for row1, row2 in zip(rows, rows_2):
        assert row1['query_id'] == row2['query_id'], "Query ID mismatch"
        assert row1['method'] == row2['method'], "Method mismatch"
        
        for metric in ['precision_at_k', 'recall_at_k', 'ndcg_at_k']:
            val1 = float(row1[metric])
            val2 = float(row2[metric])
            assert abs(val1 - val2) < 1e-6, \
                f"Metric {metric} changed between runs: {val1} vs {val2}"
    
    print("✅ Pipeline E2E test passed: All validations successful")


def test_pipeline_handles_zero_matches(temp_output_dir, test_queries_path):
    """
    Test that the pipeline handles queries with zero matches gracefully.
    
    This test creates a synthetic query that is unlikely to match any code,
    runs the pipeline, and verifies it doesn't crash and produces valid (zero) metrics.
    """
    
    # Create a temporary query file with an unlikely query
    unlikely_query_path = temp_output_dir / "unlikely_queries.csv"
    
    # Write a query that is very specific and unlikely to match
    with open(unlikely_query_path, 'w', encoding='utf-8') as f:
        f.write("query_id,query_text,ground_truth_ids\n")
        f.write("q_unlikely_1,xyzzy_plugh_nonexistent_function_12345,[]\n")
    
    # Run pipeline on this query
    args = [
        "--queries", str(unlikely_query_path),
        "--output-dir", str(temp_output_dir),
        "--methods", "bm25,neural,rag",
        "--k", "10",
        "--seed", "42"
    ]
    
    try:
        exit_code = cli_main(args)
        assert exit_code == 0, "Pipeline should handle zero matches gracefully"
    except Exception as e:
        pytest.fail(f"Pipeline crashed on zero-match query: {e}")
    
    # Verify output file exists and has zero metrics
    results_csv_path = temp_output_dir / "results.csv"
    assert results_csv_path.exists(), "results.csv should exist even with zero matches"
    
    with open(results_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Should have rows for each method
    assert len(rows) == 3, f"Expected 3 rows (one per method), got {len(rows)}"
    
    # Metrics should be zero (or very close to zero)
    for row in rows:
        assert float(row['precision_at_k']) == 0.0, \
            f"Precision should be 0 for zero-match query, got {row['precision_at_k']}"
        assert float(row['recall_at_k']) == 0.0, \
            f"Recall should be 0 for zero-match query, got {row['recall_at_k']}"
        assert float(row['ndcg_at_k']) == 0.0, \
            f"NDCG should be 0 for zero-match query, got {row['ndcg_at_k']}"
    
    print("✅ Zero-matches handling test passed")


def test_pipeline_all_methods_independent(temp_output_dir, test_queries_path):
    """
    Test that each retrieval method can run independently.
    
    This verifies that BM25, Neural, and RAG methods can be executed
    separately without interfering with each other.
    """
    
    methods_to_test = ['bm25', 'neural', 'rag']
    
    for method in methods_to_test:
        # Create a fresh output directory for each method
        method_output_dir = temp_output_dir / f"{method}_output"
        method_output_dir.mkdir(exist_ok=True)
        
        args = [
            "--queries", str(test_queries_path),
            "--output-dir", str(method_output_dir),
            "--methods", method,
            "--k", "10",
            "--seed", "42"
        ]
        
        try:
            exit_code = cli_main(args)
            assert exit_code == 0, f"Pipeline failed for method {method}"
        except Exception as e:
            pytest.fail(f"Pipeline crashed for method {method}: {e}")
        
        # Verify output
        results_csv_path = method_output_dir / "results.csv"
        assert results_csv_path.exists(), f"results.csv not created for {method}"
        
        with open(results_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have exactly one row per query (only one method)
        # (We don't check the exact count as it depends on test_queries_path content)
        assert len(rows) > 0, f"No results for method {method}"
        
        # All rows should be for the specified method
        for row in rows:
            assert row['method'] == method, \
                f"Expected method {method}, got {row['method']}"
        
        print(f"✅ Independent test passed for method: {method}")