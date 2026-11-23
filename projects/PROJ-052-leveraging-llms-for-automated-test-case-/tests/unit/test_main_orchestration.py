"""
Unit tests for main.py orchestration logic, specifically T011b (Sample Count Limit).
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_sample_limit

class TestSampleLimitOrchestration:
    """Tests for T011b: Hard stop when sample count reaches configured limit."""

    @patch('code.main.load_defects4j_data')
    @patch('code.main.load_model')
    @patch('code.main.generate_test_code')
    @patch('code.main.validate_syntax_java')
    @patch('code.main.execute_test_suite')
    @patch('code.main.check_runtime_limit')
    def test_pipeline_stops_at_sample_limit(
        self, 
        mock_runtime_check, 
        mock_exec, 
        mock_validate, 
        mock_gen, 
        mock_load_model, 
        mock_load_data
    ):
        """
        Verify that the pipeline processes exactly N samples where N is the limit,
        and stops immediately after reaching N, even if more data is available.
        """
        # Setup: Mock data with 100 items, limit is 10
        sample_limit = 10
        mock_load_data.return_value = [{"project_id": f"proj_{i}"} for i in range(100)]
        
        # Mock config to return our specific limit
        with patch('code.main.get_sample_limit', return_value=sample_limit):
            # Mock runtime check to always pass
            mock_runtime_check.return_value = True
            
            # Mock generation and validation to succeed
            mock_gen.return_value = "public class Test {}"
            mock_validate.return_value = True
            mock_exec.return_value = {"status": "success", "coverage": 0.5}
            mock_load_model.return_value = MagicMock()

            # Import and run main (isolated)
            # We need to re-import to pick up the mocked config if it was cached, 
            # but here we are patching inside the test function scope.
            # Since main.py imports at top level, we need to ensure we are testing the logic
            # by simulating the loop behavior or importing the function if refactored.
            # For this test, we will simulate the loop logic found in main.py directly
            # to avoid import side effects of a full run.
            
            from code.main import main
            
            # We cannot easily run main() and count iterations without complex mocking of sys.exit
            # Instead, we verify the logic by inspecting the mock calls on execute_test_suite
            # which is called once per processed item.
            
            # However, to be rigorous, let's just run the logic path in a controlled way
            # by extracting the loop logic or running main and checking side effects.
            # Given the constraints, we will run main() and catch sys.exit or check logs.
            
            # Simpler approach: Verify the slicing logic in the main function context.
            # Since we can't easily modify main.py to expose the loop count, 
            # we rely on the fact that execute_test_suite is called N times.
            
            # Reset mocks
            mock_exec.reset_mock()
            
            # We need to run the actual main logic but stop it cleanly.
            # The main function calls sys.exit(1) on failure, but success returns.
            # We will patch validate_all_artifacts to return True to let it finish.
            with patch('code.main.validate_all_artifacts', return_value=True):
                with patch('code.main.generate_coverage_csv'):
                    with patch('code.main.run_statistical_test'):
                        with patch('code.main.calculate_effect_size'):
                            with patch('code.main.run_power_analysis'):
                                try:
                                    main()
                                except SystemExit:
                                    pass # Expected at end of main
            
            # Assertion: execute_test_suite should be called exactly sample_limit times
            assert mock_exec.call_count == sample_limit, f"Expected {sample_limit} calls, got {mock_exec.call_count}"

    @patch('code.main.load_defects4j_data')
    @patch('code.main.load_model')
    @patch('code.main.generate_test_code')
    @patch('code.main.validate_syntax_java')
    @patch('code.main.execute_test_suite')
    @patch('code.main.check_runtime_limit')
    def test_pipeline_processes_all_if_under_limit(
        self,
        mock_runtime_check,
        mock_exec,
        mock_validate,
        mock_gen,
        mock_load_model,
        mock_load_data
    ):
        """
        Verify that if total data < limit, all items are processed.
        """
        sample_limit = 100
        total_data = 5
        mock_load_data.return_value = [{"project_id": f"proj_{i}"} for i in range(total_data)]
        
        with patch('code.main.get_sample_limit', return_value=sample_limit):
            mock_runtime_check.return_value = True
            mock_gen.return_value = "public class Test {}"
            mock_validate.return_value = True
            mock_exec.return_value = {"status": "success", "coverage": 0.5}
            mock_load_model.return_value = MagicMock()

            with patch('code.main.validate_all_artifacts', return_value=True):
                with patch('code.main.generate_coverage_csv'):
                    with patch('code.main.run_statistical_test'):
                        with patch('code.main.calculate_effect_size'):
                            with patch('code.main.run_power_analysis'):
                                try:
                                    main()
                                except SystemExit:
                                    pass

            assert mock_exec.call_count == total_data, f"Expected {total_data} calls, got {mock_exec.call_count}"
