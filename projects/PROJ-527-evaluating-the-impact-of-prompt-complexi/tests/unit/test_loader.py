"""
Unit tests for code/data/loader.py (T016).

Verifies that the loader correctly fetches the HumanEval dataset
and converts it to the expected model format.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.loader import load_human_eval_dataset
from models.data_models import HumanEvalProblem

class TestHumanEvalLoader:
    def test_loads_real_data_structure(self):
        """
        Verify that the loader returns a list of HumanEvalProblem objects
        with the correct fields when the dataset is available.
        """
        # Mock the load_dataset to return a predictable dataset
        mock_record = {
            'task_id': 'HumanEval/0',
            'prompt': 'def add(a, b):\\n    return a + b',
            'canonical_solution': 'def add(a, b):\\n    return a + b\\n',
            'test': 'assert add(1, 2) == 3',
            'entry_point': 'add'
        }

        # Create a mock dataset object that behaves like a HuggingFace Dataset
        mock_ds = MagicMock()
        mock_ds.__len__ = lambda self: 1
        mock_ds.__iter__ = lambda self: iter([mock_record])
        mock_ds.column_names = ['task_id', 'prompt', 'canonical_solution', 'test', 'entry_point']

        with patch('data.loader.load_dataset', return_value=mock_ds):
            problems = load_human_eval_dataset()

            assert isinstance(problems, list)
            assert len(problems) == 1
            
            problem = problems[0]
            assert isinstance(problem, HumanEvalProblem)
            assert problem.problem_id == 'HumanEval/0'
            assert 'add' in problem.prompt
            assert len(problem.test_list) == 1
            assert 'assert add(1, 2) == 3' in problem.test_list[0]

    def test_fails_loudly_on_fetch_error(self):
        """
        Verify that the loader raises an exception if the dataset fetch fails,
        rather than returning synthetic data or an empty list.
        """
        with patch('data.loader.load_dataset', side_effect=Exception("Network Error")):
            with pytest.raises(RuntimeError, match="Could not fetch HumanEval dataset"):
                load_human_eval_dataset()

    def test_handles_missing_fields(self):
        """
        Verify that the loader raises an error if a record is missing expected fields.
        """
        mock_record = {
            'task_id': 'HumanEval/0',
            'prompt': 'def test(): pass'
            # Missing canonical_solution, test, etc.
        }

        mock_ds = MagicMock()
        mock_ds.__len__ = lambda self: 1
        mock_ds.__iter__ = lambda self: iter([mock_record])
        mock_ds.column_names = ['task_id', 'prompt']

        with patch('data.loader.load_dataset', return_value=mock_ds):
            with pytest.raises(KeyError):
                load_human_eval_dataset()
