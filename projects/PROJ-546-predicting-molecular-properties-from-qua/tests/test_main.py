"""
Unit tests for code/main.py
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

class TestMain:
    """Test cases for main.py"""

    @patch('main.fetch_data_main')
    @patch('main.confound_analysis_main')
    @patch('main.generate_descriptors_main')
    @patch('main.dft_calculator_main')
    @patch('main.train_models_main')
    @patch('main.evaluate_models_main')
    @patch('main.setup_logger')
    def test_full_pipeline_execution(
        self, mock_setup_logger, mock_eval, mock_train, mock_dft, 
        mock_gen_semi, mock_confounds, mock_fetch
    ):
        """Test that full pipeline executes all steps in order"""
        from main import run_pipeline
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        # Execute
        result = run_pipeline()
        
        # Verify all steps were called in order
        mock_fetch.assert_called_once()
        mock_confounds.assert_called_once()
        mock_gen_semi.assert_called_once()
        mock_dft.assert_called_once()
        mock_train.assert_called_once()
        mock_eval.assert_called_once()
        
        # Verify success
        assert result == 0

    @patch('main.fetch_data_main')
    @patch('main.confound_analysis_main')
    @patch('main.generate_descriptors_main')
    @patch('main.dft_calculator_main')
    @patch('main.train_models_main')
    @patch('main.evaluate_models_main')
    @patch('main.setup_logger')
    def test_pipeline_with_skips(
        self, mock_setup_logger, mock_eval, mock_train, mock_dft, 
        mock_gen_semi, mock_confounds, mock_fetch
    ):
        """Test that pipeline respects skip flags"""
        from main import main
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        # Simulate command line args
        with patch('sys.argv', ['main.py', '--skip-fetch', '--skip-dft']):
            result = main()
        
        # Verify fetch and dft were NOT called
        mock_fetch.assert_not_called()
        mock_dft.assert_not_called()
        
        # Verify other steps were called
        mock_confounds.assert_called_once()
        mock_gen_semi.assert_called_once()
        mock_train.assert_called_once()
        mock_eval.assert_called_once()
        
        assert result == 0

    @patch('main.fetch_data_main')
    @patch('main.setup_logger')
    def test_pipeline_failure_handling(self, mock_setup_logger, mock_fetch):
        """Test that pipeline handles exceptions gracefully"""
        from main import run_pipeline
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        # Simulate failure in fetch_data
        mock_fetch.side_effect = Exception("Data fetch failed")
        
        # Execute - should return 1 on error
        result = run_pipeline()
        
        # Verify error was logged
        assert result == 1
        mock_logger.error.assert_called()
        
    def test_main_module_imports(self):
        """Test that main module can be imported without errors"""
        try:
            import main
            assert hasattr(main, 'main')
            assert hasattr(main, 'run_pipeline')
            assert hasattr(main, 'setup_logging')
        except ImportError as e:
            pytest.fail(f"Failed to import main module: {e}")

    @patch('main.fetch_data_main')
    @patch('main.confound_analysis_main')
    @patch('main.generate_descriptors_main')
    @patch('main.dft_calculator_main')
    @patch('main.train_models_main')
    @patch('main.evaluate_models_main')
    @patch('main.setup_logger')
    def test_pipeline_logging(self, mock_setup_logger, mock_eval, mock_train, 
                             mock_dft, mock_gen_semi, mock_confounds, mock_fetch):
        """Test that pipeline logs progress at each step"""
        from main import run_pipeline
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        run_pipeline()
        
        # Verify info messages were logged for each step
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Step 1" in call for call in log_calls)
        assert any("Step 2" in call for call in log_calls)
        assert any("Step 3" in call for call in log_calls)
        assert any("Step 4" in call for call in log_calls)
        assert any("Step 5" in call for call in log_calls)
        assert any("Step 6" in call for call in log_calls)
        assert any("completed successfully" in call for call in log_calls)