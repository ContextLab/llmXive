"""
Tests for the feasibility gate module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the llama_cpp import and the config
# Since we cannot run the real model in a test environment without a model file,
# we will mock the throughput measurement.

def test_measure_throughput_mocked():
    """Test measure_throughput with mocked Llama class."""
    # Mock the Llama class
    mock_llm_instance = MagicMock()
    mock_output = {
        'choices': [{'text': 'def add(a, b):\n    return a + b'}],
        'usage': {'completion_tokens': 10}
    }
    mock_llm_instance.return_value = mock_output
    
    with patch('code.feasibility_gate.Llama', mock_llm_instance):
        from code.feasibility_gate import measure_throughput
        
        # Mock time to ensure deterministic duration
        with patch('code.feasibility_gate.time.perf_counter', side_effect=[0.0, 1.0]):
            throughput, tokens = measure_throughput("/fake/path.gguf")
            
            assert throughput == 10.0
            assert tokens == 10

def test_run_feasibility_gate_passed():
    """Test run_feasibility_gate when throughput is sufficient."""
    from code.config import config
    
    with patch('code.feasibility_gate.measure_throughput', return_value=(5.0, 50)):
        from code.feasibility_gate import run_feasibility_gate
        
        # Temporarily change the log path to a temp file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        old_path = config.feasibility_log_path
        config.feasibility_log_path = tmp_path
        
        try:
            result = run_feasibility_gate()
            
            assert result['status'] == 'passed'
            assert result['proceed'] is True
            assert result['throughput'] == 5.0
            
            # Verify file was written
            assert tmp_path.exists()
            with open(tmp_path, 'r') as f:
                written_data = json.load(f)
            assert written_data['status'] == 'passed'
        finally:
            config.feasibility_log_path = old_path
            if tmp_path.exists():
                os.remove(tmp_path)

def test_run_feasibility_gate_low_throughput():
    """Test run_feasibility_gate when throughput is too low."""
    from code.config import config
    
    original_n = config.target_n
    low_throughput = 1.0 # Below default 2.0
    
    with patch('code.feasibility_gate.measure_throughput', return_value=(low_throughput, 10)):
        from code.feasibility_gate import run_feasibility_gate
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        old_path = config.feasibility_log_path
        config.feasibility_log_path = tmp_path
        
        try:
            result = run_feasibility_gate()
            
            assert result['status'] == 'low_throughput'
            assert result['proceed'] is False
            assert result['adjusted_n'] < original_n
            assert result['adjusted_n'] >= 50 # Minimum floor
            
            with open(tmp_path, 'r') as f:
                written_data = json.load(f)
            assert written_data['status'] == 'low_throughput'
        finally:
            config.feasibility_log_path = old_path
            if tmp_path.exists():
                os.remove(tmp_path)

def test_run_feasibility_gate_model_not_found():
    """Test run_feasibility_gate when model file is missing."""
    from code.feasibility_gate import run_feasibility_gate
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    # Ensure the model path doesn't exist
    fake_model_path = "/nonexistent/model.gguf"
    
    # We need to patch the config model_path temporarily
    from code.config import config
    old_model_path = config.model_path
    config.model_path = fake_model_path
    
    old_log_path = config.feasibility_log_path
    config.feasibility_log_path = tmp_path
    
    try:
        result = run_feasibility_gate()
        
        assert result['status'] == 'model_not_found'
        assert result['proceed'] is False
    finally:
        config.model_path = old_model_path
        config.feasibility_log_path = old_log_path
        if tmp_path.exists():
            os.remove(tmp_path)
