"""
Unit tests for src/scoring/run_scoring.py (T015).
Tests the orchestration logic, data loading integration, and output generation.
"""

import os
import sys
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scoring.run_scoring import (
    load_all_prompts,
    process_dataset,
    write_results,
    main
)
from src.config import DATA_DERIVED_PATH

class TestRunScoring:
    
    def test_process_dataset_empty_prompt(self):
        """Test handling of empty prompts."""
        prompts = [
            {'prompt_id': 'empty_1', 'prompt_text': '', 'source': 'test', 'reference_description': None},
            {'prompt_id': 'valid_1', 'prompt_text': 'This is a valid sentence.', 'source': 'test', 'reference_description': None}
        ]
        
        results = process_dataset(prompts)
        
        assert len(results) == 2
        
        # Check empty prompt result
        empty_res = next(r for r in results if r['prompt_id'] == 'empty_1')
        assert empty_res['normalized_score'] == 0.0
        assert empty_res['status'] == 'failed_parse'
        
        # Check valid prompt result (assuming no parse errors in helper)
        valid_res = next(r for r in results if r['prompt_id'] == 'valid_1')
        assert valid_res['status'] == 'success'
        assert 0.0 <= valid_res['normalized_score'] <= 1.0

    def test_process_dataset_malformed_text(self):
        """Test handling of non-string prompts."""
        prompts = [
            {'prompt_id': 'malformed', 'prompt_text': None, 'source': 'test', 'reference_description': None}
        ]
        
        results = process_dataset(prompts)
        
        assert len(results) == 1
        assert results[0]['normalized_score'] == 0.0
        assert results[0]['status'] == 'failed_parse'

    def test_write_results_creates_csv(self):
        """Test that write_results creates a valid CSV file."""
        results = [
            {
                'prompt_id': 'test_1',
                'source': 'test',
                'prompt_text': 'Test prompt',
                'syntactic_depth': 1.0,
                'clause_count': 1,
                'mtld': 50.0,
                'raw_score': 0.5,
                'normalized_score': 0.5,
                'status': 'success',
                'reference_description': 'ref'
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.csv')
            write_results(results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 1
                assert rows[0]['prompt_id'] == 'test_1'
                assert rows[0]['normalized_score'] == '0.5'
                assert 'syntactic_depth' in reader.fieldnames

    @patch('src.scoring.run_scoring.load_all_prompts')
    @patch('src.scoring.run_scoring.process_dataset')
    @patch('src.scoring.run_scoring.write_results')
    @patch('src.scoring.run_scoring.ensure_directories')
    def test_main_flow(self, mock_ensure, mock_write, mock_process, mock_load):
        """Test the main function flow."""
        mock_load.return_value = [{'prompt_id': '1', 'prompt_text': 'test', 'source': 't', 'reference_description': None}]
        mock_process.return_value = [{'prompt_id': '1', 'normalized_score': 0.5, 'status': 'success', 'source': 't', 'prompt_text': 'test', 'syntactic_depth': 0, 'clause_count': 0, 'mtld': 0, 'raw_score': 0, 'reference_description': None}]
        
        # Mock the output path to be in a temp dir to avoid writing to real DATA_DERIVED_PATH during test
        with patch('src.scoring.run_scoring.DATA_DERIVED_PATH', tempfile.gettempdir()):
            result_code = main()
        
        assert result_code == 0
        mock_ensure.assert_called_once()
        mock_load.assert_called_once()
        mock_process.assert_called_once()
        mock_write.assert_called_once()

    def test_load_all_prompts_integration(self):
        """
        Integration test for load_all_prompts.
        Note: This test assumes the data loaders (T006) are functional and data exists.
        If data is missing, it should raise an error or return empty list depending on implementation.
        """
        # This test is primarily to ensure the function signature and basic flow work.
        # In a real CI environment, we would mock the underlying data loaders if the raw data is large.
        # For now, we verify it doesn't crash on import and returns a list (even if empty if data missing).
        try:
            data = load_all_prompts()
            assert isinstance(data, list)
            # If data is present, check structure
            if len(data) > 0:
                assert 'prompt_id' in data[0]
                assert 'prompt_text' in data[0]
                assert 'source' in data[0]
        except RuntimeError as e:
            # Expected if no data is available in the test environment
            assert "No data loaded" in str(e)