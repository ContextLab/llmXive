"""
Tests for T011: Memory verification script.

These tests verify that the memory check logic works correctly,
mocking the heavy model loads to ensure the threshold logic is sound.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Ensure code is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def test_imports_exist():
    """Verify the script can be imported without errors (syntax check)."""
    try:
        from scripts.verify_memory_t011 import get_peak_rss_gb, load_models_and_measure, main
    except ImportError as e:
        pytest.fail(f"Failed to import T011 script: {e}")

def test_get_peak_rss_calls_process():
    """Verify that get_peak_rss_gb actually calls resource.getrusage."""
    with patch('scripts.verify_memory_t011.resource.getrusage') as mock_rusage:
        mock_rusage.return_value = MagicMock()
        mock_rusage.return_value.ru_maxrss = 1024 * 1024 * 5 # 5GB in KB
        
        from scripts.verify_memory_t011 import get_peak_rss_gb
        result = get_peak_rss_gb()
        
        mock_rusage.assert_called_once()
        assert result == 5.0

@patch('scripts.verify_memory_t011.AutoModelForCausalLM')
@patch('scripts.verify_memory_t011.AutoTokenizer')
@patch('scripts.verify_memory_t011.SentenceTransformer')
@patch('scripts.verify_memory_t011.get_peak_rss_gb')
def test_memory_limit_check_pass(mock_rss, mock_st, mock_tok, mock_model):
    """Test that the script passes when memory is under 7GB."""
    # Mock the models to avoid actual download
    mock_tok.return_value = MagicMock()
    mock_model.return_value = MagicMock()
    mock_st.return_value = MagicMock()
    
    # Simulate 4GB usage
    mock_rss.return_value = 4.0
    
    # Patch sys.exit to prevent the script from actually exiting
    with patch('scripts.verify_memory_t011.sys.exit') as mock_exit:
        # Run the core logic (we can't easily run main() with all the prints, 
        # so we test the logic flow by calling the function that would be called)
        # We will patch the load_models_and_measure to return 4.0 directly
        from scripts.verify_memory_t011 import load_models_and_measure, main
        
        # We need to test the flow inside main. 
        # Let's just verify the logic: if peak < limit, no exit(1).
        # We'll run main() with mocked dependencies.
        with patch('scripts.verify_memory_t011.load_models_and_measure', return_value=4.0):
            main()
            
            # Verify sys.exit was NOT called with 1
            # It might be called with 0 or not at all depending on implementation
            # In the script, exit(1) is only on FAIL.
            # We check that the file was written.
            output_file = Path("data/processed/memory_verification_t011.json")
            assert output_file.exists()
            
            with open(output_file) as f:
                data = json.load(f)
                assert data['status'] == 'PASS'
                assert data['peak_rss_gb'] == 4.0

@patch('scripts.verify_memory_t011.AutoModelForCausalLM')
@patch('scripts.verify_memory_t011.AutoTokenizer')
@patch('scripts.verify_memory_t011.SentenceTransformer')
@patch('scripts.verify_memory_t011.get_peak_rss_gb')
def test_memory_limit_check_fail(mock_rss, mock_st, mock_tok, mock_model):
    """Test that the script fails when memory exceeds 7GB."""
    mock_tok.return_value = MagicMock()
    mock_model.return_value = MagicMock()
    mock_st.return_value = MagicMock()
    
    # Simulate 8GB usage
    mock_rss.return_value = 8.0
    
    with patch('scripts.verify_memory_t011.sys.exit') as mock_exit:
        with patch('scripts.verify_memory_t011.load_models_and_measure', return_value=8.0):
            main()
            
            # Verify sys.exit(1) was called
            mock_exit.assert_called_once_with(1)
            
            output_file = Path("data/processed/memory_verification_t011.json")
            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                    assert data['status'] == 'FAIL'
