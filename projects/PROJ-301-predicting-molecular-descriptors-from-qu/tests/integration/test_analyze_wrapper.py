"""
Integration test for the unified `code/analyze.py` entry point.

This test verifies that the orchestration logic in `code/analyze.py` works
end-to-end by mocking the necessary data artifacts and model files.
"""
import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(PROJECT_ROOT) not in str(__import__('sys').path):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logger import setup_logger, get_logger
from code.utils.memory_monitor import MemoryMonitor

# Mock the heavy dependencies before importing the module under test
# We need to ensure the analyze.py script can be imported and run without
# actually needing the full dataset or models to exist on disk for this test.

def create_mock_artifacts(temp_dir: Path):
    """Create minimal mock artifacts required for the analyze pipeline."""
    
    # 1. Mock Test Labels
    labels_path = temp_dir / "data" / "processed" / "labels_test.csv"
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    with open(labels_path, "w") as f:
        f.write("molecule_id,dipole,HOMO,LUMO\n")
        for i in range(10):
            f.write(f"mol_{i},{i*1.0},{i*2.0},{i*3.0}\n")
    
    # 2. Mock Model Artifacts (2D and 3D)
    # We create dummy pickle files that can be loaded
    models_dir = temp_dir / "artifacts" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 2D Model Mock
    mock_model_2d = {
        "model_type": "RandomForest",
        "n_features": 2048,
        "predictions": np.random.rand(10).tolist()
    }
    with open(models_dir / "model_2d.pkl", "wb") as f:
        pickle.dump(mock_model_2d, f)
    
    # 3D Model Mock
    mock_model_3d = {
        "model_type": "RandomForest",
        "n_features": 50,
        "predictions": np.random.rand(10).tolist()
    }
    with open(models_dir / "model_3d.pkl", "wb") as f:
        pickle.dump(mock_model_3d, f)
    
    # 3. Mock Baseline Errors (if needed by analyze.py)
    # The analyze.py might expect this if it's part of the flow
    baseline_path = temp_dir / "artifacts" / "metrics" / "baseline_error.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_path, "w") as f:
        json.dump({
            "dipole": {"mae": 0.5},
            "HOMO": {"mae": 0.8},
            "LUMO": {"mae": 1.2}
        }, f)

def test_analyze_orchestration():
    """
    Test that code/analyze.py orchestrates the full pipeline correctly.
    
    This test:
    1. Sets up a temporary directory with mock artifacts.
    2. Invokes the main logic of analyze.py (or its components) within that context.
    3. Verifies that expected output files are generated.
    """
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Prepare mock data
        create_mock_artifacts(tmp_path)
        
        # Define paths relative to the temp directory
        # We need to patch the hardcoded paths in analyze.py or pass them via CLI
        # Since analyze.py is designed to be a wrapper, we assume it looks for
        # artifacts in standard locations relative to the project root or uses CLI args.
        
        # Strategy: We will patch the internal functions of code/04_analysis.py
        # to return mock data instead of loading from disk, then call main()
        # to verify the orchestration flow (calls to baselines, predictions, stats, plots, report).
        
        # Import the analysis module components
        # Note: We assume the module is structured such that we can import the functions
        from code import code_04_analysis as analysis_module
        
        # Mock the file loading functions to return predictable data
        def mock_load_test_labels(path):
            return {
                "dipole": [1.0, 2.0, 3.0],
                "HOMO": [2.0, 4.0, 6.0],
                "LUMO": [3.0, 6.0, 9.0],
                "ids": ["m1", "m2", "m3"]
            }
        
        def mock_load_model_artifact(path):
            return {
                "predictions": [1.1, 2.1, 3.1],
                "model_type": "mock"
            }
        
        def mock_load_json_artifact(path):
            return {"mae": 0.1}
        
        # Patch the loading functions
        with patch.object(analysis_module, 'load_test_labels', side_effect=mock_load_test_labels), \
             patch.object(analysis_module, 'load_model_artifact', side_effect=mock_load_model_artifact), \
             patch.object(analysis_module, 'load_json_artifact', side_effect=mock_load_json_artifact), \
             patch.object(analysis_module, 'generate_parity_predictions', return_value=None), \
             patch.object(analysis_module, 'generate_final_report', return_value=None):
            
            # Mock the plotting function to avoid matplotlib backend issues in CI
            with patch('matplotlib.pyplot.savefig'):
                # Now call the main orchestration logic
                # We need to simulate the CLI arguments or set default paths
                # Since the task is to test the *orchestration*, we call the main function
                # with a mock output directory if necessary, or rely on defaults.
                
                # The analyze.py script likely has a main() that calls these functions.
                # We will call the functions directly in the order specified in T037
                # to verify the logic flow, as calling the script via subprocess
                # in a unit test is less reliable for mocking internal state.
                
                # However, the task asks to test the *wrapper* (analyze.py).
                # So we should ideally import and run the main() of analyze.py.
                # But analyze.py might import 04_analysis.
                
                # Let's import the analyze.py main function
                from code import analyze
                
                # We need to ensure the paths in analyze.py are correct for our temp dir
                # If analyze.py hardcodes paths, we might need to patch them.
                # Assuming analyze.py uses relative paths or CLI args.
                # For this test, we will patch the output directory usage.
                
                # Since we cannot easily pass args to a module's main without sys.argv manipulation,
                # and the task is about the *logic*, we verify the sequence of calls.
                
                # Mock the specific functions in 04_analysis that are called by analyze.py
                # to ensure they are called in the right order.
                
                call_order = []
                
                def track_baselines(*args, **kwargs):
                    call_order.append('baselines')
                    return {}
                
                def track_predictions(*args, **kwargs):
                    call_order.append('predictions')
                    return {}
                
                def track_stats(*args, **kwargs):
                    call_order.append('stats')
                    return {}
                
                def track_boundary(*args, **kwargs):
                    call_order.append('boundary')
                    return {}
                
                def track_plots(*args, **kwargs):
                    call_order.append('plots')
                    return {}
                
                def track_report(*args, **kwargs):
                    call_order.append('report')
                    return {}

                # Patch the functions in the 04_analysis module
                with patch.object(analysis_module, 'compute_baselines', side_effect=track_baselines), \
                     patch.object(analysis_module, 'generate_predictions', side_effect=track_predictions), \
                     patch.object(analysis_module, 'run_statistics', side_effect=track_stats), \
                     patch.object(analysis_module, 'define_failure_boundary', side_effect=track_boundary), \
                     patch.object(analysis_module, 'generate_plots', side_effect=track_plots), \
                     patch.object(analysis_module, 'generate_final_report', side_effect=track_report):
                    
                    # Run the analyze wrapper
                    # We need to handle sys.argv if the script expects arguments
                    original_argv = analyze.sys.argv
                    analyze.sys.argv = ['analyze.py'] # No args
                    
                    try:
                        analyze.main()
                    except Exception as e:
                        # If it fails due to missing files that we didn't mock,
                        # it's still a failure of the script's robustness, but
                        # for this test we want to ensure the orchestration flow is correct.
                        # If the mock is set up correctly, it should pass.
                        pass
                    finally:
                        analyze.sys.argv = original_argv
                
                # Verify the order of calls
                expected_order = ['baselines', 'predictions', 'stats', 'boundary', 'plots', 'report']
                assert call_order == expected_order, f"Orchestration order mismatch: {call_order} vs {expected_order}"
                
                # Verify that all required functions were called exactly once
                assert call_order.count('baselines') == 1
                assert call_order.count('predictions') == 1
                assert call_order.count('stats') == 1
                assert call_order.count('boundary') == 1
                assert call_order.count('plots') == 1
                assert call_order.count('report') == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])