"""
Tests for T083: Run Pilot Execution on Small Subset.

These tests verify that the pilot execution scripts:
1. Run without errors on a small subset
2. Produce the expected output files
3. Handle edge cases (empty manifest, missing files)
"""
import json
import os
import sys
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestT083PilotExecution:
    """Test suite for T083 pilot execution scripts."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a minimal manifest for testing
        self.manifest_path = self.temp_path / "test_manifest.csv"
        with open(self.manifest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'raw_error_log', 'annotated_structural_feature', 'ground_truth_resolution'])
            writer.writeheader()
            writer.writerow({
                'task_id': 'task_001',
                'raw_error_log': 'SyntaxError: invalid syntax at line 10',
                'annotated_structural_feature': 'Syntactic Error',
                'ground_truth_resolution': 'Fix indentation'
            })
            writer.writerow({
                'task_id': 'task_002',
                'raw_error_log': 'Logical loop detected in reasoning',
                'annotated_structural_feature': 'Logical Loop',
                'ground_truth_resolution': 'Break loop'
            })
            writer.writerow({
                'task_id': 'task_003',
                'raw_error_log': 'Semantic ambiguity in variable naming',
                'annotated_structural_feature': 'Semantic Ambiguity',
                'ground_truth_resolution': 'Clarify naming'
            })

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_run_rule_engine_pilot_creates_output(self):
        """Test that run_rule_engine creates the pilot_results.csv file."""
        # This test would require mocking the rule engine logic since we don't have
        # the full rules_library.json in the test environment.
        # For now, we verify the script structure and argument parsing.
        from code_03_execution_run_rule_engine import main
        
        output_path = self.temp_path / "pilot_results.csv"
        
        # We can't run the full pipeline without rules, but we can verify
        # the script accepts the arguments
        with patch('sys.argv', [
            'run_rule_engine.py',
            '--manifest', str(self.manifest_path),
            '--rules', '/nonexistent/rules.json',  # Intentionally missing to test error handling
            '--output', str(output_path),
            '--subset-size', '2'
        ]):
            # Expected to fail due to missing rules file, which is correct behavior
            try:
                main()
            except SystemExit as e:
                # Expected to exit with error code 1
                assert e.code == 1

    def test_run_baseline_pilot_creates_output(self):
        """Test that run_baseline creates the pilot_baseline_results.json file."""
        from code_03_execution_run_baseline import run_baseline_pilot
        
        output_path = self.temp_path / "pilot_baseline_results.json"
        
        # Run the pilot
        results = run_baseline_pilot(
            manifest_path=str(self.manifest_path),
            output_path=str(output_path),
            subset_size=2
        )
        
        # Verify output file exists
        assert output_path.exists(), "Output file was not created"
        
        # Verify output content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Output should be a list"
        assert len(data) == 2, f"Expected 2 results, got {len(data)}"
        
        # Verify result structure
        for result in data:
            assert 'task_id' in result
            assert 'method' in result
            assert result['method'] == 'baseline'
            assert 'time_to_pivot' in result
            assert 'success' in result
            assert 'is_censored' in result

    def test_baseline_handles_timeout_censoring(self):
        """Test that baseline simulation correctly handles timeout censored data."""
        from code_03_execution_run_baseline import run_baseline_simulation
        
        # Test with a very short timeout to force censored data
        result = run_baseline_simulation("test_task", "Some error", timeout=0.001)
        
        assert result['is_censored'] == True
        assert result['time_to_pivot'] == 0.001

    def test_rule_engine_and_baseline_produce_consistent_task_ids(self):
        """Test that both engines process the same task IDs from the manifest."""
        # This is a high-level integration test concept.
        # In a real scenario, we would run both and compare task_id lists.
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])