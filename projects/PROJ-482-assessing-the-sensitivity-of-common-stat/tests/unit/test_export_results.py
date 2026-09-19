"""
Unit tests for export_results.py (Task T029).
"""
import os
import tempfile
import shutil
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# We need to mock the dependencies that might not be fully ready or 
# to isolate the export logic.
# However, the task requires real execution. We test the structure.

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_ensure_output_dirs_creates_directories(temp_output_dir):
    """Test that ensure_output_dirs creates the necessary folders."""
    import sys
    sys.path.insert(0, 'code')
    from export_results import ensure_output_dirs
    
    # Temporarily patch the default path logic if needed, 
    # but here we just check the function runs without error 
    # and creates dirs if we set a custom root.
    # Since the function uses hardcoded relative paths, we test it in a temp context.
    
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        ensure_output_dirs()
        assert os.path.exists(os.path.join(temp_output_dir, 'data/processed'))
        assert os.path.exists(os.path.join(temp_output_dir, 'data/processed/plots'))
    finally:
        os.chdir(original_cwd)

def test_export_final_results_calls_exporter(temp_output_dir):
    """Test that export_final_results calls the underlying exporter."""
    import sys
    sys.path.insert(0, 'code')
    
    # Mock the export_results_to_csv from analyzer
    with patch('export_results.export_results_to_csv') as mock_export:
        from export_results import export_final_results
        
        df = pd.DataFrame({'a': [1, 2]})
        path = os.path.join(temp_output_dir, 'test.csv')
        
        export_final_results(df, path)
        
        mock_export.assert_called_once_with(df, path)

def test_save_plots_calls_generator(temp_output_dir):
    """Test that save_plots calls the visualizer generator."""
    import sys
    sys.path.insert(0, 'code')
    
    # Mock the generate_all_plots from visualizer
    with patch('export_results.generate_all_plots') as mock_gen:
        mock_gen.return_value = ['plot1.png', 'plot2.png']
        from export_results import save_plots
        
        df = pd.DataFrame({'a': [1, 2]})
        path = os.path.join(temp_output_dir, 'plots')
        
        result = save_plots(df, path)
        
        mock_gen.assert_called_once_with(df, path)
        assert result == ['plot1.png', 'plot2.png']

def test_main_raises_on_missing_input(temp_output_dir):
    """Test that main raises FileNotFoundError if input is missing."""
    import sys
    sys.path.insert(0, 'code')
    
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_output_dir)
        # Ensure the input file path doesn't exist
        input_path = os.path.join(temp_output_dir, 'data/processed/raw_pvalues.csv')
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        
        from export_results import main
        
        with pytest.raises(FileNotFoundError):
            main()
    finally:
        os.chdir(original_cwd)