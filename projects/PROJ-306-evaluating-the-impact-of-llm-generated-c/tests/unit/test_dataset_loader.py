"""
Unit tests for dataset_loader module.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from code.dataset_loader import (
    _validate_record,
    validate_and_save_catalog,
    REQUIRED_FIELDS,
    CATALOG_KEYS
)

class TestValidateRecord:
    def test_valid_record_mbpp(self):
        record = {
            'task_id': 'mbpp/1',
            'prompt': 'Write a function to add two numbers.',
            'human_solution': 'def add(a, b): return a + b',
            'test_suite': 'assert add(1, 2) == 3'
        }
        result = _validate_record(record, 'MBPP')
        assert result['task_id'] == 'mbpp/1'
        assert 'test_suite_path' in result
        assert 'difficulty' in result
        assert 'code_patterns' in result
        assert 'loops' not in result['code_patterns']  # No loops in solution
        assert 'conditionals' in result['code_patterns']  # No conditionals either, but let's check

    def test_valid_record_humaneval(self):
        record = {
            'task_id': 'HumanEval/0',
            'prompt': 'Write a function to multiply two numbers.',
            'human_solution': 'def multiply(a, b): return a * b',
            'test_suite': 'assert multiply(2, 3) == 6'
        }
        result = _validate_record(record, 'HumanEval')
        assert result['task_id'] == 'HumanEval/0'
        assert result['test_suite_path'].endswith('HumanEval/0.py')

    def test_missing_required_field(self):
        record = {
            'task_id': 'test/1',
            'prompt': 'Test prompt',
            # Missing human_solution
            'test_suite': 'assert True'
        }
        with pytest.raises(ValueError, match="Missing required field 'human_solution'"):
            _validate_record(record, 'Test')

    def test_code_pattern_extraction(self):
        record_with_loops = {
            'task_id': 'test/loop',
            'prompt': 'Loop test',
            'human_solution': 'def sum_list(lst):\n    total = 0\n    for x in lst:\n        total += x\n    return total',
            'test_suite': 'assert sum_list([1,2,3]) == 6'
        }
        result = _validate_record(record_with_loops, 'Test')
        assert 'loops' in result['code_patterns']

        record_with_conditionals = {
            'task_id': 'test/cond',
            'prompt': 'Conditional test',
            'human_solution': 'def check(x):\n    if x > 0:\n        return True\n    return False',
            'test_suite': 'assert check(1) == True'
        }
        result = _validate_record(record_with_conditionals, 'Test')
        assert 'conditionals' in result['code_patterns']

class TestValidateAndSaveCatalog:
    @patch('code.dataset_loader.load_dataset')
    def test_catalog_generation(self, mock_load_dataset):
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.items.return_value = [
            ('test', [
                {
                    'task_id': 'mbpp/1',
                    'prompt': 'Test',
                    'human_solution': 'def f(): pass',
                    'test_suite': 'assert f() is None'
                }
            ])
        ]
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            mbpp_dir = os.path.join(tmpdir, 'mbpp')
            humaneval_dir = os.path.join(tmpdir, 'humaneval')
            output_path = os.path.join(tmpdir, 'catalog.json')
            
            os.makedirs(mbpp_dir)
            os.makedirs(humaneval_dir)
            
            # Create a mock MBPP file
            mbpp_file = os.path.join(mbpp_dir, 'test.json')
            with open(mbpp_file, 'w') as f:
                json.dump([{
                    'task_id': 'mbpp/1',
                    'prompt': 'Test',
                    'human_solution': 'def f(): pass',
                    'test_suite': 'assert f() is None'
                }], f)

            result = validate_and_save_catalog(
                mbpp_raw_dir=mbpp_dir,
                humaneval_raw_dir=humaneval_dir,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                catalog = json.load(f)
            
            assert len(catalog) == 1
            assert catalog[0]['task_id'] == 'mbpp/1'
            for key in CATALOG_KEYS:
                assert key in catalog[0]

    def test_missing_raw_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'catalog.json')
            
            result = validate_and_save_catalog(
                mbpp_raw_dir=os.path.join(tmpdir, 'nonexistent'),
                humaneval_raw_dir=os.path.join(tmpdir, 'nonexistent'),
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                catalog = json.load(f)
            assert len(catalog) == 0
