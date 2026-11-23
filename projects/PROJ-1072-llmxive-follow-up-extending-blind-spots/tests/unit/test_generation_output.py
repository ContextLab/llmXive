import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code_02_generate_cot import process_tasks, generate_cot_trace, generate_prompt

def test_process_tasks_writes_immediately():
    """Test that process_tasks writes to file immediately upon generation."""
    # Create a mock model and tokenizer
    mock_model = Mock()
    mock_tokenizer = Mock()
    
    # Create sample tasks
    tasks = [
        {"id": "task_1", "instruction": "Test instruction 1", "constraint": "Test constraint 1"},
        {"id": "task_2", "instruction": "Test instruction 2", "constraint": "Test constraint 2"}
    ]
    
    # Mock the generate_cot_trace function to return a trace
    with patch('code_02_generate_cot.generate_cot_trace', return_value="Generated trace for task"):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tmp:
            output_path = Path(tmp.name)
            
            # Call process_tasks
            process_tasks(mock_model, mock_tokenizer, tasks, output_path)
            
            # Verify the file was created and contains valid JSONL
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            
            # Check each line is valid JSON
            for line in lines:
                data = json.loads(line)
                assert "task_id" in data
                assert "cot_trace" in data
                assert data["status"] == "success"
    
    # Clean up
    output_path.unlink()

def test_process_tasks_handles_failures():
    """Test that process_tasks handles generation failures gracefully."""
    mock_model = Mock()
    mock_tokenizer = Mock()
    
    tasks = [
        {"id": "task_1", "instruction": "Test instruction", "constraint": "Test constraint"}
    ]
    
    # Mock generate_cot_trace to return None (failure)
    with patch('code_02_generate_cot.generate_cot_trace', return_value=None):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tmp:
            output_path = Path(tmp.name)
            
            success, failed = process_tasks(mock_model, mock_tokenizer, tasks, output_path)
            
            assert success == 0
            assert failed == 1
            
            # Verify the file contains the failed record
            with open(output_path, 'r') as f:
                data = json.loads(f.read())
                assert data["status"] == "failed"
                assert data["cot_trace"] is None
    
    output_path.unlink()

def test_generate_prompt_format():
    """Test that generate_prompt creates the correct format."""
    task = {
        "instruction": "Solve this puzzle.",
        "constraint": "Use only geometric shapes."
    }
    
    prompt = generate_prompt(task)
    
    assert "Task: Solve this puzzle." in prompt
    assert "IMPORTANT CONSTRAINT: Use only geometric shapes." in prompt
    assert "step-by-step reasoning" in prompt.lower()
    assert "constraint" in prompt.lower()