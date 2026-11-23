"""
Integration test for T021: run_inference.py
Verifies that the script runs end-to-end and produces expected artifacts.
"""
import os
import sys
import json
import tempfile
import shutil
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.run_inference import (
    main,
    load_prompts,
    load_corpus,
    prepare_prompt,
    save_translation,
    run_inference_for_entry,
    PROMPT_CONDITIONS
)
from src.utils.logging import get_logger

@pytest.fixture
def temp_dirs():
    """Create temporary directories for data/prompts, data/processed, and data/evaluation."""
    base = tempfile.mkdtemp()
    data_dir = Path(base) / "data"
    prompts_dir = data_dir / "prompts"
    processed_dir = data_dir / "processed"
    eval_dir = data_dir / "evaluation"
    
    prompts_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy prompt files
    for cond in PROMPT_CONDITIONS:
        (prompts_dir / f"{cond}.txt").write_text(f"Please translate this Python code:\n{cond}\n{{python_code}}")
    
    # Create dummy corpus
    corpus_path = processed_dir / "corpus.csv"
    with open(corpus_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'python_code', 'javascript_code'])
        writer.writeheader()
        writer.writerow({
            'id': 'test_001',
            'python_code': 'print("hello")',
            'javascript_code': 'console.log("hello");'
        })
        writer.writerow({
            'id': 'test_002',
            'python_code': 'x = 1 + 2',
            'javascript_code': 'var x = 1 + 2;'
        })
    
    yield {
        'base': base,
        'data': data_dir,
        'prompts': prompts_dir,
        'processed': processed_dir,
        'eval': eval_dir,
        'corpus': corpus_path
    }
    
    shutil.rmtree(base)

@patch('src.execution.run_inference.call_inference_api')
@patch('src.execution.run_inference.PROJECT_ROOT')
def test_run_inference_creates_artifacts(mock_root, mock_api, temp_dirs):
    """
    Test that running the inference script creates the expected directory structure
    and JSON files for translations.
    """
    # Mock the project root to point to our temp directory
    mock_root.return_value = temp_dirs['base'].parent
    
    # Mock the API response to return a deterministic string
    mock_api.return_value = "console.log('translated');"
    
    # Patch the specific paths used by the script
    with patch.object(sys.modules['src.execution.run_inference'], 'DATA_DIR', temp_dirs['data']), \
         patch.object(sys.modules['src.execution.run_inference'], 'PROCESSED_CORPUS', temp_dirs['corpus']), \
         patch.object(sys.modules['src.execution.run_inference'], 'RAW_TRANSLATIONS_DIR', temp_dirs['eval'] / 'raw_translations'), \
         patch.object(sys.modules['src.execution.run_inference'], 'LOGS_DIR', temp_dirs['eval'] / 'logs'):
        
        main()
    
    # Verify output directory structure
    raw_trans_dir = temp_dirs['eval'] / 'raw_translations'
    assert raw_trans_dir.exists(), "raw_translations directory should be created"
    
    for cond in PROMPT_CONDITIONS:
        cond_dir = raw_trans_dir / cond
        assert cond_dir.exists(), f"Directory for condition {cond} should be created"
        
        # Check for JSON files
        json_files = list(cond_dir.glob("*.json"))
        assert len(json_files) > 0, f"Should have created JSON files for condition {cond}"
        
        # Validate content of one file
        sample_file = json_files[0]
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        assert 'id' in data
        assert 'raw_output' in data
        assert 'python_code' in data
        assert data['condition'] == cond

@patch('src.execution.run_inference.call_inference_api')
@patch('src.execution.run_inference.PROJECT_ROOT')
def test_timeout_handling(mock_root, mock_api, temp_dirs):
    """
    Test that the script handles API timeouts gracefully (logs error, continues).
    """
    mock_root.return_value = temp_dirs['base'].parent
    
    # Simulate a timeout on the first call, success on the second
    from src.utils.timeout_utils import TimeoutError as ApiTimeoutError
    
    call_count = 0
    def mock_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ApiTimeoutError("Simulated timeout")
        return "success_output"
    
    mock_api.side_effect = mock_side_effect
    
    with patch.object(sys.modules['src.execution.run_inference'], 'DATA_DIR', temp_dirs['data']), \
         patch.object(sys.modules['src.execution.run_inference'], 'PROCESSED_CORPUS', temp_dirs['corpus']), \
         patch.object(sys.modules['src.execution.run_inference'], 'RAW_TRANSLATIONS_DIR', temp_dirs['eval'] / 'raw_translations'), \
         patch.object(sys.modules['src.execution.run_inference'], 'LOGS_DIR', temp_dirs['eval'] / 'logs'):
        
        main()
    
    # Should have created files for successful runs
    # (Note: exact count depends on how many entries/conditions exist, but should not crash)
    raw_trans_dir = temp_dirs['eval'] / 'raw_translations'
    assert raw_trans_dir.exists()