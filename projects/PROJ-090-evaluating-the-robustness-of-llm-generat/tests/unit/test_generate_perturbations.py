import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data.generate_perturbations import (
    load_humaneval_tasks,
    generate_and_filter_perturbations,
    save_results,
    save_candidates_pool,
    SEMANTIC_THRESHOLD
)
from data.perturbations import generate_perturbation_variants
from data.semantic_validator import compute_similarity
from config import get_budget_generations
from utils.state import set_budget_caps, reset_state

class TestPerturbationGeneration:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset state before each test."""
        reset_state()
        set_budget_caps(generations=1000, samples=1000)
        yield
        reset_state()

    @patch('data.generate_perturbations.load_dataset')
    def test_load_humaneval_tasks(self, mock_load):
        """Test that HumanEval loading works correctly."""
        mock_dataset = [
            {"task_id": "HumanEval/0", "prompt": "def test(): pass", "canonical_solution": "", "test": ""},
            {"task_id": "HumanEval/1", "prompt": "def foo(): pass", "canonical_solution": "", "test": ""}
        ]
        mock_load.return_value = MagicMock(__iter__=lambda self: iter(mock_dataset))
        
        tasks = load_humaneval_tasks()
        
        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "HumanEval/0"
        assert tasks[0]["prompt"] == "def test(): pass"

    def test_generate_and_filter_perturbations_logic(self):
        """
        Test the core logic of generation and filtering.
        We mock the generation and similarity functions to control the flow.
        """
        tasks = [
            {"task_id": "T1", "prompt": "original A", "canonical_solution": "", "test": ""},
            {"task_id": "T2", "prompt": "original B", "canonical_solution": "", "test": ""}
        ]
        
        # Mock variants generator
        def mock_gen_variants(prompt):
            if prompt == "original A":
                return [("synonym", "synonym A"), ("typo", "typo A")]
            return [("rephrase", "rephrase B")]
        
        # Mock similarity
        def mock_sim(model, orig, pert):
            if pert == "synonym A":
                return 0.96 # Valid
            if pert == "typo A":
                return 0.94 # Invalid
            if pert == "rephrase B":
                return 0.98 # Valid
            return 0.0
        
        with patch('data.generate_perturbations.generate_perturbation_variants', side_effect=mock_gen_variants):
            with patch('data.generate_perturbations.compute_similarity', side_effect=mock_sim):
                with patch('data.generate_perturbations.get_model', return_value=MagicMock()):
                    primary, candidates = generate_and_filter_perturbations(tasks, budget_limit=10)
        
        # Check candidates
        assert len(candidates) == 3
        # T1: synonym (0.96), typo (0.94)
        # T2: rephrase (0.98)
        
        # Check validity
        valid_synonym = next(c for c in candidates if c["perturbation_type"] == "synonym")
        assert valid_synonym["is_valid"] is True
        assert valid_synonym["raw_score"] == 0.96
        
        valid_typo = next(c for c in candidates if c["perturbation_type"] == "typo")
        assert valid_typo["is_valid"] is False
        assert valid_typo["raw_score"] == 0.94
        
        # Check primary set
        assert len(primary) == 2
        # T1 should have synonym (0.96)
        t1_primary = next(p for p in primary if p["task_id"] == "T1")
        assert t1_primary["perturbation_type"] == "synonym"
        assert t1_primary["raw_score"] == 0.96
        
        # T2 should have rephrase (0.98)
        t2_primary = next(p for p in primary if p["task_id"] == "T2")
        assert t2_primary["perturbation_type"] == "rephrase"
        assert t2_primary["raw_score"] == 0.98

    def test_save_results_creates_file(self, tmp_path):
        """Test that save_results creates a valid JSON file."""
        data = [
            {"task_id": "T1", "perturbed_prompt": "test", "raw_score": 0.99}
        ]
        output_file = tmp_path / "test_results.json"
        
        save_results(data, output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]["task_id"] == "T1"

    def test_save_candidates_pool_creates_file(self, tmp_path):
        """Test that save_candidates_pool creates a valid JSON file."""
        data = [
            {"task_id": "T1", "is_valid": True},
            {"task_id": "T1", "is_valid": False}
        ]
        output_file = tmp_path / "test_candidates.json"
        
        save_candidates_pool(data, output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            loaded = json.load(f)
        assert len(loaded) == 2

    def test_threshold_strictness(self):
        """Verify that the threshold is strictly > 0.95."""
        assert SEMANTIC_THRESHOLD == 0.95
        
        # Simulate a score exactly at 0.95
        score_exact = 0.95
        assert score_exact > SEMANTIC_THRESHOLD is False, "0.95 must be invalid"
        
        score_high = 0.950001
        assert score_high > SEMANTIC_THRESHOLD is True, "0.950001 must be valid"