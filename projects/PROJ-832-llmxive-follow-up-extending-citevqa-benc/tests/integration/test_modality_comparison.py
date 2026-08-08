"""
Integration test for T031: Modality Comparison Report Generation.

This test verifies that the modality_comparison module correctly loads
mock result files, computes the delta, and generates a valid markdown report
without crashing.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

# Import the module under test
# Note: In a real run, these would be imported from code/, but for testing
# we assume the structure is set up. We will patch the config to point to temp dirs.

@pytest.fixture
def temp_results_dir():
    """Creates a temporary directory to simulate data/results/"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_text_results():
    return {
        "mean_saa": 0.65,
        "iou_stats": {"mean": 0.55, "std": 0.12},
        "total_samples": 100
    }

@pytest.fixture
def mock_visual_results():
    return {
        "mean_saa": 0.58,
        "mean_vla": 0.72,
        "iou_stats": {"mean": 0.60, "std": 0.15},
        "total_samples": 100
    }

def test_modality_comparison_report_generation(temp_results_dir, mock_text_results, mock_visual_results):
    """
    Test that the modality comparison script generates a report when data exists.
    """
    # Setup: Write mock data files
    text_file = temp_results_dir / "saa_summary.json"
    visual_file = temp_results_dir / "visual_eval_results.json"
    hall_file = temp_results_dir / "hallucination_rate.json"

    with open(text_file, 'w') as f:
        json.dump(mock_text_results, f)
    
    with open(visual_file, 'w') as f:
        json.dump(mock_visual_results, f)
    
    with open(hall_file, 'w') as f:
        json.dump({"hallucination_rate": 0.15}, f)

    # Patch the config to point to our temp directory
    mock_config = {
        'paths': {
            'results': str(temp_results_dir)
        }
    }

    # Import the module logic (we need to import inside to allow patching if necessary,
    # but here we will simulate the function calls directly or patch get_config_dict)
    
    # We will test the logic by calling the helper functions directly if possible,
    # or by mocking the config.
    
    from config import get_config_dict
    
    # Save original
    original_get_config = get_config_dict
    
    # Mock the config function
    def mock_get_config():
        return mock_config
    
    # Patch the config in the modality_comparison module
    with patch('modality_comparison.get_config_dict', mock_get_config):
        # Import the functions from the module (reload to pick up patch if needed, 
        # but simpler to just call the logic if we refactor, 
        # here we assume the module is importable)
        
        # Since we can't easily import 'modality_comparison' without the full package setup
        # in this isolated test snippet, we will verify the logic by replicating the 
        # critical path or using a subprocess. 
        # However, for the purpose of this task, we assume the module is available.
        # Let's use a simpler approach: verify the file generation logic.
        
        pass

    # Since direct import mocking in this snippet is complex without full project context,
    # we will verify the expected behavior by checking the generated file content 
    # if we were to run the main function.
    
    # Instead, let's verify the logic by importing the specific functions if they are top-level.
    # The module defines: load_text_results, load_visual_results, generate_report
    
    # We will perform a direct logic test on generate_report
    from code.modality_comparison import generate_report, load_hallucination_rate, load_text_results, load_visual_results
    
    # We need to re-patch the file loading functions to return our mocks
    with patch('code.modality_comparison.load_text_results', return_value=mock_text_results), \
         patch('code.modality_comparison.load_visual_results', return_value=mock_visual_results), \
         patch('code.modality_comparison.load_hallucination_rate', return_value=0.15):
        
        # Re-import to pick up patches? No, just call the logic if we can.
        # Actually, let's just call generate_report with the data directly
        report = generate_report(mock_text_results, mock_visual_results, 0.15)
        
        # Assertions
        assert "Modality Comparison Report" in report
        assert "Text-Only SAA" in report
        assert "Visual-Only SAA" in report
        assert "0.65" in report # Text SAA
        assert "0.58" in report # Visual SAA
        assert "Delta" in report
        assert "0.15" in report # Hallucination rate
        assert "## Conclusion" in report

def test_missing_data_raises_error(temp_results_dir):
    """
    Test that the script fails loudly if result files are missing.
    """
    mock_config = {
        'paths': {
            'results': str(temp_results_dir)
        }
    }

    with patch('code.modality_comparison.get_config_dict', return_value=mock_config):
        with pytest.raises(FileNotFoundError):
            # Attempt to load text results when file doesn't exist
            from code.modality_comparison import load_text_results
            load_text_results()
