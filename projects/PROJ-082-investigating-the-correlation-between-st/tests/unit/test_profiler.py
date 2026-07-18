import pytest
import time
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Mock the logger to avoid file writing issues in tests
import sys
from unittest.mock import MagicMock

mock_logger = MagicMock()
sys.modules['utils.logger'] = MagicMock(get_logger=lambda x: mock_logger)
sys.modules['utils.config'] = MagicMock(
    get_project_root=lambda: Path(tempfile.gettempdir()),
    ensure_directory=lambda x: None
)

# Now import the module after mocking dependencies
from utils.profiler import profile_pipeline_entrypoint, save_profile_results, MAX_RUNTIME_SECONDS

class TestProfiler:
    def test_profile_decorator_runtime_check_pass(self):
        """Test that a fast function passes the runtime check."""
        @profile_pipeline_entrypoint
        def fast_func():
            time.sleep(0.1)
            return "done"
        
        result = fast_func()
        assert result == "done"

    def test_profile_decorator_runtime_check_fail(self):
        """Test that a slow function raises RuntimeError."""
        @profile_pipeline_entrypoint
        def slow_func():
            time.sleep(MAX_RUNTIME_SECONDS + 1)
            return "done"
        
        with pytest.raises(RuntimeError, match="exceeded 15-minute limit"):
            slow_func()

    def test_save_profile_results_structure(self):
        """Test that profile results are saved with correct structure."""
        # Create a mock profiler
        profiler = MagicMock()
        profiler.disable = MagicMock()
        
        # Mock pstats to return predictable data
        with patch('utils.profiler.pstats') as mock_pstats:
            mock_stats_instance = MagicMock()
            mock_stats_instance.sort_stats = MagicMock()
            mock_stats_instance.print_stats = MagicMock()
            mock_stats_instance.stats = {
                ('test.py', 1, 'func'): (1, 1, 0.01, 0.02, {})
            }
            mock_pstats.Stats.return_value = mock_stats_instance
            
            with patch('utils.profiler.io.StringIO') as mock_stringio:
                mock_stringio.return_value.getvalue.return_value = "Mock stats text"
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch('utils.profiler.get_project_root') as mock_root:
                        mock_root.return_value = Path(tmpdir)
                        with patch('utils.profiler.ensure_directory'):
                            save_profile_results(profiler, 0.5)
                            
                            output_file = Path(tmpdir) / "data" / "logs" / "profile_results.json"
                            # Ensure directory exists for check
                            output_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Re-run save to actual file for verification logic
                            # (The mock above prevented actual file write in the patch, 
                            # so we verify the logic via the mock calls or a real minimal run)
                            pass
        
        # Verify the logic via a real minimal run
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir)
            with patch('utils.profiler.get_project_root', return_value=test_path):
                with patch('utils.profiler.ensure_directory'):
                    # Create a real cProfile to test the save function logic
                    import cProfile
                    p = cProfile.Profile()
                    p.enable()
                    time.sleep(0.01)
                    p.disable()
                    
                    save_profile_results(p, 0.01)
                    
                    output_file = test_path / "data" / "logs" / "profile_results.json"
                    assert output_file.exists()
                    
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                    
                    assert "total_runtime_seconds" in data
                    assert "top_functions" in data
                    assert "status" in data
                    assert data["status"] == "passed"

    def test_profile_decorator_calls_save(self):
        """Test that the decorator calls save_profile_results."""
        with patch('utils.profiler.save_profile_results') as mock_save:
            @profile_pipeline_entrypoint
            def dummy():
                return True
            
            dummy()
            mock_save.assert_called_once()