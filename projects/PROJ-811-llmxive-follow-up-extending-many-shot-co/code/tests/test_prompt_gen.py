import pytest
import random
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code/src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.prompt_gen import PromptGenerator

@pytest.fixture
def sample_dag_manifest():
    """Sample DAG manifest data for testing."""
    return [
        {
            "id": "ex1",
            "question": "What is 2+2?",
            "answer": "4",
            "thought": "Add 2 and 2.",
            "logical_difficulty": 1,
            "depth": 1,
            "curvature_score": 0.8
        },
        {
            "id": "ex2",
            "question": "Solve for x: 2x = 10",
            "answer": "5",
            "thought": "Divide both sides by 2.",
            "logical_difficulty": 3,
            "depth": 3,
            "curvature_score": 0.5
        },
        {
            "id": "ex3",
            "question": "Calculate the area of a circle with radius 3.",
            "answer": "28.27",
            "thought": "Use formula pi*r^2.",
            "logical_difficulty": 2,
            "depth": 2,
            "curvature_score": 0.6
        }
    ]

@pytest.fixture
def temp_manifest_file(sample_dag_manifest):
    """Creates a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_dag_manifest, f)
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)

class TestLogicalAscendingSort:
    def test_sort_by_depth(self, sample_dag_manifest):
        generator = PromptGenerator()
        sorted_examples = generator.sort_by_logical_ascending(sample_dag_manifest)
        
        depths = [ex["depth"] for ex in sorted_examples]
        assert depths == sorted(depths), "Examples should be sorted by depth ascending"
        assert depths[0] == 1
        assert depths[-1] == 3

class TestDeterministicShuffling:
    def test_shuffle_with_seed(self, sample_dag_manifest):
        generator = PromptGenerator()
        seed = 42
        
        # Shuffle twice with same seed
        shuffled1 = generator.shuffle_deterministic(sample_dag_manifest, seed)
        shuffled2 = generator.shuffle_deterministic(sample_dag_manifest, seed)
        
        assert shuffled1 == shuffled2, "Shuffling with same seed should be deterministic"
        
        # Ensure order changed (unless list is trivial or unlucky, but with 3 items and seed 42 it likely changes)
        # We check that the set of IDs is the same
        ids1 = [ex["id"] for ex in shuffled1]
        ids2 = [ex["id"] for ex in sample_dag_manifest]
        assert set(ids1) == set(ids2), "Shuffling should preserve all examples"

class TestPromptAssembly:
    def test_assemble_prompt_with_examples(self, sample_dag_manifest):
        generator = PromptGenerator()
        prompt = generator.assemble_prompt(sample_dag_manifest)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Check that all questions are present
        for ex in sample_dag_manifest:
            assert ex["question"] in prompt

    def test_assemble_prompt_empty(self):
        generator = PromptGenerator()
        prompt = generator.assemble_prompt([])
        assert prompt == ""

    def test_assemble_prompt_without_query_placeholder(self):
        generator = PromptGenerator()
        prompt = generator.assemble_prompt(sample_dag_manifest, include_query=False)
        assert "Question:\nAnswer:" not in prompt

class TestStrategyGeneration:
    def test_logical_ascending_strategy(self, sample_dag_manifest):
        generator = PromptGenerator()
        prompt = generator.generate_prompt_for_strategy(sample_dag_manifest, "logical_ascending")
        assert len(prompt) > 0
        assert sample_dag_manifest[0]["question"] in prompt

    def test_logical_random_strategy(self, sample_dag_manifest):
        generator = PromptGenerator()
        prompt = generator.generate_prompt_for_strategy(sample_dag_manifest, "logical_random", seed=42)
        assert len(prompt) > 0

    def test_original_cds_strategy(self, sample_dag_manifest):
        generator = PromptGenerator()
        prompt = generator.generate_prompt_for_strategy(sample_dag_manifest, "original_cds")
        assert len(prompt) > 0

    def test_invalid_strategy(self, sample_dag_manifest):
        generator = PromptGenerator()
        with pytest.raises(ValueError):
            generator.generate_prompt_for_strategy(sample_dag_manifest, "invalid_strategy")

    def test_missing_seed_for_random(self, sample_dag_manifest):
        generator = PromptGenerator()
        with pytest.raises(ValueError):
            generator.generate_prompt_for_strategy(sample_dag_manifest, "logical_random")

class TestPromptGeneratorConfig:
    def test_custom_template(self):
        config = {
            "prompt": {
                "template": "SYSTEM: {system}\n",
                "example_template": "Q: {question}\nA: {answer}\n",
                "separator": " | ",
                "system_prompt": "You are a helpful assistant.",
                "final_suffix": "Q:\nA:"
            }
        }
        generator = PromptGenerator(config)
        
        examples = [
            {"question": "Test?", "answer": "Ok"}
        ]
        prompt = generator.assemble_prompt(examples)
        
        assert "SYSTEM: You are a helpful assistant." in prompt
        assert "Q: Test?\nA: Ok" in prompt
        assert " | " in prompt
        assert prompt.endswith("Q:\nA:")