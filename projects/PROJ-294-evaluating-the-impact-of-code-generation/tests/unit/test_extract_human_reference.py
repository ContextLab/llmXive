"""
Unit tests for T011: extract_human_reference.py
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import the function to test
from extract_human_reference import extract_human_references


def test_extract_human_references_creates_jsonl():
    """Test that the function creates a valid JSONL file."""
    # Create temporary directory and files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.parquet")
        output_path = os.path.join(tmpdir, "output.jsonl")
        
        # Create mock parquet data
        data = {
            "task_id": ["HumanEval/0", "HumanEval/1"],
            "prompt": ["def add(a, b):\n    pass", "def multiply(a, b):\n    pass"],
            "canonical_solution": ["return a + b", "return a * b"],
            "test": ["", ""],
            "entry_point": ["add", "multiply"]
        }
        df = pd.DataFrame(data)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, input_path)
        
        # Run extraction
        count = extract_human_references(input_path, output_path)
        
        # Verify count
        assert count == 2
        
        # Verify output file exists and is valid JSONL
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2
        
        # Verify JSON structure
        for line in lines:
            record = json.loads(line)
            assert "task_id" in record
            assert "prompt" in record
            assert "canonical_solution" in record
            assert isinstance(record["task_id"], str)
            assert isinstance(record["prompt"], str)
            assert isinstance(record["canonical_solution"], str)


def test_extract_human_references_preserves_fields():
    """Test that task_id and prompt fields are preserved exactly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.parquet")
        output_path = os.path.join(tmpdir, "output.jsonl")
        
        # Create mock data with specific values
        test_task_id = "HumanEval/42"
        test_prompt = "def factorial(n):\n    \"\"\"Compute factorial of n.\"\"\"\n    pass"
        test_solution = "if n <= 1:\n    return 1\nreturn n * factorial(n-1)"
        
        data = {
            "task_id": [test_task_id],
            "prompt": [test_prompt],
            "canonical_solution": [test_solution],
            "test": [""],
            "entry_point": ["factorial"]
        }
        df = pd.DataFrame(data)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, input_path)
        
        # Run extraction
        extract_human_references(input_path, output_path)
        
        # Verify output
        with open(output_path, "r") as f:
            record = json.loads(f.readline())
        
        assert record["task_id"] == test_task_id
        assert record["prompt"] == test_prompt
        assert record["canonical_solution"] == test_solution


def test_extract_human_references_raises_on_missing_input():
    """Test that function raises RuntimeError for missing input file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "nonexistent.parquet")
        output_path = os.path.join(tmpdir, "output.jsonl")
        
        with pytest.raises(RuntimeError, match="Input file not found"):
            extract_human_references(input_path, output_path)