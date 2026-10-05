"""
Integration tests for src/cli/main.py
Tests the CLI orchestration, edge cases, and output schema.
"""
import os
import sys
import json
import tempfile
import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.main import (
    load_queries,
    load_index_data,
    calculate_metrics,
    save_results_csv,
    save_throughput_report,
    main
)
from src.data.models import RetrievalMethod, QueryResult

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_processed_data():
    """Create mock preprocessed data for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create queries file
        queries_path = tmpdir / "queries.jsonl"
        queries = [
            {"query_id": "q1", "query": "sort list", "ground_truth_ids": ["c1", "c2"]},
            {"query_id": "q2", "query": "read file", "ground_truth_ids": ["c3"]},
            {"query_id": "q3", "query": "", "ground_truth_ids": ["c4"]},  # Empty query
        ]
        with open(queries_path, 'w') as f:
            for q in queries:
                f.write(json.dumps(q) + '\n')
        
        # Create index file
        index_path = tmpdir / "snippets.jsonl"
        snippets = [
            {"snippet_id": "c1", "code": "def sort_list(lst): return sorted(lst)"},
            {"snippet_id": "c2", "code": "def sort_data(data): data.sort()"},
            {"snippet_id": "c3", "code": "def read_file(path): open(path).read()"},
            {"snippet_id": "c4", "code": "def empty_func(): pass"},
        ]
        with open(index_path, 'w') as f:
            for s in snippets:
                f.write(json.dumps(s) + '\n')
        
        yield queries_path, index_path

def test_cli_output_schema(temp_output_dir, mock_processed_data):
    """Test that CLI produces CSV with correct schema."""
    queries_path, index_path = mock_processed_data
    
    # Mock the retrieval functions to return deterministic results
    with patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
         patch('src.cli.main.evaluate_bm25') as mock_eval_bm25, \
         patch('src.cli.main.load_neural_retriever') as mock_neural, \
         patch('src.cli.main.evaluate_neural') as mock_eval_neural, \
         patch('src.cli.main.create_rag_pipeline') as mock_rag, \
         patch('src.cli.main.evaluate_rag') as mock_eval_rag:
        
        # Setup mocks
        mock_bm25.return_value = MagicMock()
        mock_eval_bm25.return_value = ["c1", "c2"]
        
        mock_neural.return_value = MagicMock()
        mock_eval_neural.return_value = ["c2", "c1"]
        
        mock_rag.return_value = MagicMock()
        mock_eval_rag.return_value = ["c1"]
        
        # Run main with specific args
        sys.argv = [
            'main.py',
            '--queries', str(queries_path),
            '--index', str(index_path),
            '--output-dir', str(temp_output_dir),
            '--k', '5',
            '--methods', 'bm25', 'neural'
        ]
        
        main()
        
        # Verify output files exist
        results_csv = temp_output_dir / "results.csv"
        throughput_json = temp_output_dir / "throughput_report.json"
        
        assert results_csv.exists(), "results.csv should be created"
        assert throughput_json.exists(), "throughput_report.json should be created"
        
        # Verify CSV schema
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check headers
            expected_headers = {
                'query_id', 'method', 'precision_at_k', 'recall_at_k',
                'ndcg_at_k', 'num_retrieved', 'num_ground_truth'
            }
            assert set(reader.fieldnames) == expected_headers, f"Expected headers {expected_headers}, got {set(reader.fieldnames)}"
            
            # Check data rows
            assert len(rows) > 0, "Should have at least one result row"
            for row in rows:
                assert 'query_id' in row
                assert 'method' in row
                assert row['method'] in ['bm25', 'neural', 'rag']
                assert 'precision_at_k' in row
                assert 'recall_at_k' in row
                assert 'ndcg_at_k' in row
                assert 'num_retrieved' in row
                assert 'num_ground_truth' in row
        
        # Verify throughput JSON schema
        with open(throughput_json, 'r') as f:
            throughput_data = json.load(f)
            assert 'total_queries' in throughput_data
            assert 'total_time_seconds' in throughput_data
            assert 'queries_per_hour' in throughput_data
            
            # Verify throughput is NOT in CSV
            with open(results_csv, 'r') as f:
                csv_content = f.read()
                assert 'queries_per_hour' not in csv_content, "Throughput should NOT be in results.csv"

def test_cli_handles_zero_matches(temp_output_dir, mock_processed_data):
    """Test that CLI handles queries with zero matches gracefully."""
    queries_path, index_path = mock_processed_data
    
    with patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
         patch('src.cli.main.evaluate_bm25') as mock_eval_bm25, \
         patch('src.cli.main.load_neural_retriever') as mock_neural, \
         patch('src.cli.main.evaluate_neural') as mock_eval_neural:
        
        mock_bm25.return_value = MagicMock()
        mock_eval_bm25.return_value = []  # Zero matches
        
        mock_neural.return_value = MagicMock()
        mock_eval_neural.return_value = []  # Zero matches
        
        sys.argv = [
            'main.py',
            '--queries', str(queries_path),
            '--index', str(index_path),
            '--output-dir', str(temp_output_dir),
            '--k', '5',
            '--methods', 'bm25', 'neural'
        ]
        
        # Should not raise exception
        main()
        
        # Verify output exists
        results_csv = temp_output_dir / "results.csv"
        assert results_csv.exists()
        
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should have rows even with zero matches
            assert len(rows) > 0
            
            # Verify num_retrieved is 0 for zero-match cases
            for row in rows:
                if row['num_retrieved'] == '0':
                    # Metrics should be 0.0
                    assert float(row['precision_at_k']) == 0.0
                    assert float(row['recall_at_k']) == 0.0
                    assert float(row['ndcg_at_k']) == 0.0

def test_cli_handles_empty_queries(temp_output_dir, mock_processed_data):
    """Test that CLI skips empty queries."""
    queries_path, index_path = mock_processed_data
    
    with patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
         patch('src.cli.main.evaluate_bm25') as mock_eval_bm25:
        
        mock_bm25.return_value = MagicMock()
        mock_eval_bm25.return_value = ["c1"]
        
        sys.argv = [
            'main.py',
            '--queries', str(queries_path),
            '--index', str(index_path),
            '--output-dir', str(temp_output_dir),
            '--k', '5',
            '--methods', 'bm25'
        ]
        
        main()
        
        # Empty query should be skipped, so we should have fewer rows than queries
        results_csv = temp_output_dir / "results.csv"
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # We have 3 queries, but one is empty, so should have 2 rows
            assert len(rows) == 2
            
            # Verify empty query (q3) is not in results
            query_ids = [row['query_id'] for row in rows]
            assert 'q3' not in query_ids, "Empty query should be skipped"

def test_cli_handles_no_ground_truth(temp_output_dir, mock_processed_data):
    """Test that CLI handles queries with no ground truth."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create queries with no ground truth
        queries_path = tmpdir / "queries.jsonl"
        queries = [
            {"query_id": "q1", "query": "test", "ground_truth_ids": []},
        ]
        with open(queries_path, 'w') as f:
            for q in queries:
                f.write(json.dumps(q) + '\n')
        
        # Create index
        index_path = tmpdir / "snippets.jsonl"
        snippets = [{"snippet_id": "c1", "code": "def test(): pass"}]
        with open(index_path, 'w') as f:
            for s in snippets:
                f.write(json.dumps(s) + '\n')
        
        with patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
             patch('src.cli.main.evaluate_bm25') as mock_eval_bm25:
            
            mock_bm25.return_value = MagicMock()
            mock_eval_bm25.return_value = ["c1"]
            
            sys.argv = [
                'main.py',
                '--queries', str(queries_path),
                '--index', str(index_path),
                '--output-dir', str(temp_output_dir),
                '--k', '5',
                '--methods', 'bm25'
            ]
            
            main()
            
            # Should still produce output
            results_csv = temp_output_dir / "results.csv"
            assert results_csv.exists()
            
            with open(results_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                
                # With no ground truth, metrics should be 0
                assert float(rows[0]['precision_at_k']) == 0.0
                assert float(rows[0]['recall_at_k']) == 0.0
                assert float(rows[0]['ndcg_at_k']) == 0.0

def test_cli_all_methods(temp_output_dir, mock_processed_data):
    """Test that CLI runs all specified methods."""
    queries_path, index_path = mock_processed_data
    
    with patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
         patch('src.cli.main.evaluate_bm25') as mock_eval_bm25, \
         patch('src.cli.main.load_neural_retriever') as mock_neural, \
         patch('src.cli.main.evaluate_neural') as mock_eval_neural, \
         patch('src.cli.main.create_rag_pipeline') as mock_rag, \
         patch('src.cli.main.evaluate_rag') as mock_eval_rag:
        
        mock_bm25.return_value = MagicMock()
        mock_eval_bm25.return_value = ["c1"]
        
        mock_neural.return_value = MagicMock()
        mock_eval_neural.return_value = ["c2"]
        
        mock_rag.return_value = MagicMock()
        mock_eval_rag.return_value = ["c1", "c2"]
        
        sys.argv = [
            'main.py',
            '--queries', str(queries_path),
            '--index', str(index_path),
            '--output-dir', str(temp_output_dir),
            '--k', '5',
            '--methods', 'bm25', 'neural', 'rag'
        ]
        
        main()
        
        results_csv = temp_output_dir / "results.csv"
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            methods_found = set(row['method'] for row in rows)
            assert 'bm25' in methods_found
            assert 'neural' in methods_found
            assert 'rag' in methods_found