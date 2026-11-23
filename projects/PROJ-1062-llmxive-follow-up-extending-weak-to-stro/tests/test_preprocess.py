"""
Tests for the data preprocessing module (T006).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.preprocess import format_prompt, extract_reasoning_step, process_record, main
import code.data.preprocess as preprocess_module

def test_format_prompt():
    """Test prompt formatting function."""
    problem_text = "What is 2 + 2?"
    problem_id = "AIME_2024_001"
    
    result = format_prompt(problem_text, problem_id)
    
    assert "Problem ID: AIME_2024_001" in result
    assert "Question: What is 2 + 2?" in result
    assert result.startswith("Problem ID:")
    
def test_extract_reasoning_step_with_solution():
    """Test extraction when 'solution' field is present."""
    record = {
        "id": "123",
        "question": "Calculate 5*5",
        "solution": "5 times 5 is 25."
    }
    
    result = extract_reasoning_step(record)
    assert result == "5 times 5 is 25."
    
def test_extract_reasoning_step_with_reasoning():
    """Test extraction when 'reasoning' field is present."""
    record = {
        "id": "123",
        "question": "Calculate 5*5",
        "reasoning": "Multiplication of 5 by 5 yields 25."
    }
    
    result = extract_reasoning_step(record)
    assert result == "Multiplication of 5 by 5 yields 25."
    
def test_extract_reasoning_step_with_answer():
    """Test extraction when only 'answer' field is present."""
    record = {
        "id": "123",
        "question": "Calculate 5*5",
        "answer": "25"
    }
    
    result = extract_reasoning_step(record)
    assert result == "The answer is: 25"
    
def test_extract_reasoning_step_missing():
    """Test that extraction fails when no reasoning field exists."""
    record = {
        "id": "123",
        "question": "Calculate 5*5",
        "metadata": "some data"
    }
    
    try:
        extract_reasoning_step(record)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
        
def test_process_record():
    """Test full record processing."""
    raw_record = {
        "id": "AIME_001",
        "question": "Find the value of x.",
        "solution": "x equals 42."
    }
    
    result = process_record(raw_record)
    
    assert result["id"] == "AIME_001"
    assert "Question: Find the value of x." in result["prompt"]
    assert result["reasoning"] == "x equals 42."
    assert result["raw"] == raw_record
    
def test_main_with_missing_input():
    """Test that main raises error when input file is missing."""
    # Temporarily change the input path to a non-existent file
    with patch.object(preprocess_module, 'INPUT_PATH', Path("/tmp/nonexistent.jsonl")):
        try:
            main()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass
            
def test_main_processing_flow():
    """Test the main processing flow with mock data."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.jsonl"
        output_path = Path(tmpdir) / "output.jsonl"
        checksum_path = Path(tmpdir) / "checksum.sha256"
        
        # Write mock input data
        mock_data = [
            {"id": "1", "question": "Q1", "solution": "A1"},
            {"id": "2", "question": "Q2", "reasoning": "R2"}
        ]
        
        with open(input_path, "w") as f:
            for item in mock_data:
                f.write(json.dumps(item) + "\n")
                
        # Mock the module paths
        with patch.object(preprocess_module, 'INPUT_PATH', input_path), \
             patch.object(preprocess_module, 'OUTPUT_PATH', output_path), \
             patch.object(preprocess_module, 'CHECKSUM_FILE', checksum_path):
            
            result = main()
            
            assert result == 0
            assert output_path.exists()
            assert checksum_path.exists()
            
            # Verify output content
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                first_record = json.loads(lines[0])
                assert first_record["id"] == "1"
                assert first_record["reasoning"] == "A1"