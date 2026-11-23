"""
Integration test for T063: Positional Sensitivity for Instructions.

Tests the full pipeline of generating shifted variants and comparing pass rates.
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

from prompts.position_tester import (
    extract_constraint_from_prompt,
    generate_positional_variants,
    run_positional_sensitivity_test,
    write_results_to_csv
)
from config import Paths


class TestExtractConstraint:
    def test_extract_constraint_at_start(self):
        prompt = "Constraint: Do not use loops.\n\nWrite a function..."
        block, remaining = extract_constraint_from_prompt(prompt)
        assert block is not None
        assert "Constraint" in block
        assert "Write a function" in remaining

    def test_extract_constraint_not_found(self):
        prompt = "Write a function to sort a list."
        result = extract_constraint_from_prompt(prompt)
        assert result is None

    def test_extract_constraint_in_middle(self):
        prompt = "Write a function.\n\nConstraint: No loops allowed.\n\nReturn result."
        block, remaining = extract_constraint_from_prompt(prompt)
        assert block is not None
        assert "Constraint" in block


class TestGeneratePositionalVariants:
    @pytest.fixture
    def mock_variants_df(self):
        data = {
            'problem_id': ['P1', 'P2', 'P3'],
            'variant_id': ['V1', 'V2', 'V3'],
            'complexity_label': ['simple', 'complex', 'very_complex'],
            'prompt_text': [
                "Simple prompt.",
                "Complex prompt.\n\nConstraint: No loops.\n\nMore text.",
                "Very complex.\n\nLimitation: Use recursion.\n\nEnd."
            ]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_problems_dict(self):
        return {
            'P1': {'task_id': 'P1', 'prompt': 'Simple', 'canonical_solution': 'sol', 'test': [], 'entry_point': 'f'},
            'P2': {'task_id': 'P2', 'prompt': 'Complex', 'canonical_solution': 'sol', 'test': [], 'entry_point': 'f'},
            'P3': {'task_id': 'P3', 'prompt': 'Very', 'canonical_solution': 'sol', 'test': [], 'entry_point': 'f'}
        }

    def test_generates_shifted_variants(self, mock_variants_df, mock_problems_dict):
        result = generate_positional_variants(mock_variants_df, mock_problems_dict)
        # Should only generate for 'complex' and 'very_complex'
        assert len(result) == 2
        assert result[0]['original_label'] == 'complex'
        assert result[1]['original_label'] == 'very_complex'
        # Check that shifted prompt contains the constraint at the end
        assert "Constraint: No loops." in result[0]['shifted_prompt']
        assert "Limitation: Use recursion." in result[1]['shifted_prompt']


class TestRunPositionalSensitivityTest:
    @pytest.fixture
    def mock_variants_df(self):
        data = {
            'problem_id': ['P1'],
            'variant_id': ['V1'],
            'complexity_label': ['complex'],
            'prompt_text': ['Complex prompt.\n\nConstraint: No loops.\n\nMore text.'],
            'token_count': [100],
            'structural_element_count': [{'examples': 0, 'constraints': 1, 'steps': 0}]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_problems_dict(self):
        return {
            'P1': {
                'task_id': 'P1', 
                'prompt': 'Complex', 
                'canonical_solution': 'def f(): pass', 
                'test': ['assert f() == 1'], 
                'entry_point': 'f'
            }
        }

    @patch('prompts.position_tester.process_problem')
    @patch('prompts.position_tester.execute_sample')
    def test_run_with_mocked_llm_and_execution(
        self, mock_execute, mock_process, mock_variants_df, mock_problems_dict
    ):
        # Mock LLM response
        mock_process.return_value = {'code': 'def f(): return 1', 'metadata': {}}
        
        # Mock execution result
        mock_result = MagicMock()
        mock_result.pass_count = 1
        mock_result.fail_count = 0
        mock_execute.return_value = mock_result

        results = run_positional_sensitivity_test(mock_variants_df, mock_problems_dict, sample_size=1)
        
        assert len(results) == 1
        assert results[0]['problem_id'] == 'P1'
        assert results[0]['original_label'] == 'complex'
        assert results[0]['shifted_label'] == 'shifted'
        assert results[0]['original_pass'] == 1.0
        assert results[0]['shifted_pass'] == 1.0


class TestWriteResultsToCsv:
    def test_writes_correct_columns(self, tmp_path):
        results = [
            {
                "problem_id": "P1",
                "original_label": "complex",
                "shifted_label": "shifted",
                "original_pass": 1.0,
                "shifted_pass": 0.5
            }
        ]
        output_path = tmp_path / "positional_sensitivity.csv"
        write_results_to_csv(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['problem_id'] == 'P1'
            assert float(rows[0]['original_pass']) == 1.0
            assert float(rows[0]['shifted_pass']) == 0.5
            assert 'original_pass' in rows[0]
            assert 'shifted_pass' in rows[0]
            assert 'problem_id' in rows[0]
            assert 'original_label' in rows[0]
            assert 'shifted_label' in rows[0]