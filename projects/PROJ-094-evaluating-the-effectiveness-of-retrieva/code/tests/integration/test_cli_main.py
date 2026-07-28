"""
Integration tests for src/cli/main.py (T013).
Verifies the CLI orchestrates methods, handles edge cases, and produces valid CSV output.
"""
import os
import sys
import json
import tempfile
import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data.models import RetrievalMethod
from src.models.metrics import precision_at_k, recall_at_k, ndcg_at_k

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_processed_data():
    """Create a mock processed JSONL file with valid structure."""
    data = [
        {
            "query": "def sort_list(arr):",
            "code": "def sort_list(arr):\n    return sorted(arr)",
            "language": "python",
            "ground_truth_ids": ["doc_1"],
            "id": "query_1"
        },
        {
            "query": "how to read file",
            "code": "with open('file.txt') as f: print(f.read())",
            "language": "python",
            "ground_truth_ids": ["doc_2", "doc_3"],
            "id": "query_2"
        },
        {
            "query": "",  # Empty query edge case
            "code": "pass",
            "language": "python",
            "ground_truth_ids": [],
            "id": "query_3"
        },
        {
            "query": "calculate sum",
            "code": "sum([1,2,3])",
            "language": "python",
            "ground_truth_ids": [],  # No ground truth edge case
            "id": "query_4"
        }
    ]
    return data

def test_cli_output_schema(temp_output_dir, mock_processed_data, tmp_path):
    """Test that CLI produces a CSV with the expected schema."""
    # Setup mock data file
    mock_data_path = tmp_path / "data" / "processed" / "python_processed.jsonl"
    mock_data_path.parent.mkdir(parents=True)
    
    with open(mock_data_path, 'w', encoding='utf-8') as f:
        for item in mock_processed_data:
            f.write(json.dumps(item) + '\n')

    # Mock the retrievers to return deterministic results
    mock_retrieved_docs_bm25 = [{"id": "doc_1", "code": "mock"}]
    mock_retrieved_docs_neural = [{"id": "doc_2", "code": "mock"}]
    mock_retrieved_docs_rag = [{"id": "doc_1", "code": "mock"}, {"id": "doc_3", "code": "mock"}]

    output_path = temp_output_dir / "results.csv"

    with patch('src.cli.main.PROCESSED_DATA_PATH', mock_data_path), \
         patch('src.cli.main.load_bm25_retriever') as mock_bm25_load, \
         patch('src.cli.main.load_neural_retriever') as mock_neural_load, \
         patch('src.cli.main.create_rag_pipeline') as mock_rag_load, \
         patch('src.cli.main.evaluating_bm25') as mock_eval_bm25, \
         patch('src.cli.main.evaluating_neural') as mock_eval_neural, \
         patch('src.cli.main.evaluating_rag') as mock_eval_rag:

        # Setup mocks
        mock_bm25_load.return_value.search.return_value = mock_retrieved_docs_bm25
        mock_neural_load.return_value.search.return_value = mock_retrieved_docs_neural
        
        mock_rag_instance = MagicMock()
        mock_rag_instance.process_query.return_value = {"retrieved_docs": mock_retrieved_docs_rag}
        mock_rag_load.return_value = mock_rag_instance

        # Mock evaluation functions to return known metrics
        def mock_eval_bm25_impl(retrieved_ids, gt_ids, k_vals):
            return {
                "precision@k": {k: 1.0 if gt_ids else 0.0 for k in k_vals},
                "recall@k": {k: 1.0 if gt_ids else 0.0 for k in k_vals},
                "ndcg@k": {k: 1.0 if gt_ids else 0.0 for k in k_vals}
            }
        
        mock_eval_bm25.side_effect = mock_eval_bm25_impl
        mock_eval_neural.side_effect = mock_eval_bm25_impl
        mock_eval_rag.side_effect = mock_eval_bm25_impl

        # Run CLI
        sys.argv = [
            'main.py',
            '--num-queries', '2',
            '--k-values', '5',
            '--methods', 'bm25',
            '--output', str(output_path),
            '--log-level', 'ERROR'
        ]
        
        # Import and run main
        from src.cli.main import main
        main()

    # Verify output exists
    assert output_path.exists(), "Output CSV was not created"

    # Verify schema
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0, "Output CSV is empty"
    
    # Check required columns
    required_cols = {"method", "query_id", "num_retrieved", "precision@5", "recall@5", "ndcg@5"}
    actual_cols = set(rows[0].keys())
    assert required_cols.issubset(actual_cols), f"Missing columns: {required_cols - actual_cols}"

    # Verify method values
    methods = {row["method"] for row in rows}
    assert methods == {"bm25"}, f"Unexpected methods: {methods}"

def test_cli_handles_zero_matches(temp_output_dir, mock_processed_data, tmp_path):
    """Test that CLI handles queries with zero matches gracefully."""
    mock_data_path = tmp_path / "data" / "processed" / "python_processed.jsonl"
    mock_data_path.parent.mkdir(parents=True)
    
    with open(mock_data_path, 'w', encoding='utf-8') as f:
        for item in mock_processed_data:
            f.write(json.dumps(item) + '\n')

    # Mock retriever to return empty list
    mock_retrieved_docs = []
    output_path = temp_output_dir / "results_zero.csv"

    with patch('src.cli.main.PROCESSED_DATA_PATH', mock_data_path), \
         patch('src.cli.main.load_bm25_retriever') as mock_bm25_load:
        
        mock_bm25_load.return_value.search.return_value = mock_retrieved_docs

        sys.argv = [
            'main.py',
            '--num-queries', '1',
            '--k-values', '5',
            '--methods', 'bm25',
            '--output', str(output_path),
            '--log-level', 'ERROR'
        ]

        from src.cli.main import main
        main()

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have a row with 0 retrieved
    assert len(rows) == 1
    assert int(rows[0]["num_retrieved"]) == 0
    assert float(rows[0]["precision@5"]) == 0.0

def test_cli_handles_empty_queries(temp_output_dir, mock_processed_data, tmp_path):
    """Test that CLI skips queries with empty text."""
    mock_data_path = tmp_path / "data" / "processed" / "python_processed.jsonl"
    mock_data_path.parent.mkdir(parents=True)
    
    with open(mock_data_path, 'w', encoding='utf-8') as f:
        for item in mock_processed_data:
            f.write(json.dumps(item) + '\n')

    output_path = temp_output_dir / "results_empty.csv"

    with patch('src.cli.main.PROCESSED_DATA_PATH', mock_data_path), \
         patch('src.cli.main.load_bm25_retriever') as mock_bm25_load:
        
        mock_bm25_load.return_value.search.return_value = [{"id": "doc_1"}]

        sys.argv = [
            'main.py',
            '--num-queries', '4',  # Includes empty query
            '--k-values', '5',
            '--methods', 'bm25',
            '--output', str(output_path),
            '--log-level', 'ERROR'
        ]

        from src.cli.main import main
        main()

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have fewer rows than queries (empty one skipped)
    # We have 4 queries, 1 is empty, so max 3 rows if others have GT
    # Query 4 has no GT, so skipped too. So 2 rows (query 1, 2)
    assert len(rows) <= 3, "Empty query should be skipped"

def test_cli_handles_no_ground_truth(temp_output_dir, mock_processed_data, tmp_path):
    """Test that CLI skips queries with no ground truth labels."""
    mock_data_path = tmp_path / "data" / "processed" / "python_processed.jsonl"
    mock_data_path.parent.mkdir(parents=True)
    
    with open(mock_data_path, 'w', encoding='utf-8') as f:
        for item in mock_processed_data:
            f.write(json.dumps(item) + '\n')

    output_path = temp_output_dir / "results_no_gt.csv"

    with patch('src.cli.main.PROCESSED_DATA_PATH', mock_data_path), \
         patch('src.cli.main.load_bm25_retriever') as mock_bm25_load:
        
        mock_bm25_load.return_value.search.return_value = [{"id": "doc_1"}]

        sys.argv = [
            'main.py',
            '--num-queries', '4',
            '--k-values', '5',
            '--methods', 'bm25',
            '--output', str(output_path),
            '--log-level', 'ERROR'
        ]

        from src.cli.main import main
        main()

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Query 4 has no GT, so it should be skipped
    # Query 3 has empty text, so it should be skipped
    # Only 2 rows expected (query 1 and 2)
    assert len(rows) == 2

def test_cli_all_methods(temp_output_dir, mock_processed_data, tmp_path):
    """Test that CLI runs all three methods when requested."""
    mock_data_path = tmp_path / "data" / "processed" / "python_processed.jsonl"
    mock_data_path.parent.mkdir(parents=True)
    
    with open(mock_data_path, 'w', encoding='utf-8') as f:
        for item in mock_processed_data:
            f.write(json.dumps(item) + '\n')

    output_path = temp_output_dir / "results_all.csv"

    with patch('src.cli.main.PROCESSED_DATA_PATH', mock_data_path), \
         patch('src.cli.main.load_bm25_retriever') as mock_bm25, \
         patch('src.cli.main.load_neural_retriever') as mock_neural, \
         patch('src.cli.main.create_rag_pipeline') as mock_rag:

        mock_bm25.return_value.search.return_value = [{"id": "doc_1"}]
        mock_neural.return_value.search.return_value = [{"id": "doc_2"}]
        mock_rag.return_value.process_query.return_value = {"retrieved_docs": [{"id": "doc_3"}]}

        sys.argv = [
            'main.py',
            '--num-queries', '2',
            '--k-values', '5',
            '--methods', 'bm25', 'neural', 'rag',
            '--output', str(output_path),
            '--log-level', 'ERROR'
        ]

        from src.cli.main import main
        main()

    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    methods = {row["method"] for row in rows}
    assert methods == {"bm25", "neural", "rag"}, f"Missing methods: {methods}"
    # 2 queries * 3 methods = 6 rows
    assert len(rows) == 6