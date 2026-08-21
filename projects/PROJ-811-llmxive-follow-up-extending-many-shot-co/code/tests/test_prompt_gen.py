"""
Tests for prompt generation module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.prompt_gen import PromptGenerator


@pytest.fixture
def sample_dag_manifest():
    """Create a sample DAG manifest for testing."""
    return [
        {
            'id': 'trace_1',
            'input': 'What is 2+2?',
            'output': '4',
            'logical_difficulty': 1,
            'depth': 1
        },
        {
            'id': 'trace_2',
            'input': 'What is 3+3?',
            'output': '6',
            'logical_difficulty': 2,
            'depth': 2
        },
        {
            'id': 'trace_3',
            'input': 'What is 4+4?',
            'output': '8',
            'logical_difficulty': 3,
            'depth': 3
        },
        {
            'id': 'trace_4',
            'input': 'What is 5+5?',
            'output': '10',
            'logical_difficulty': 2,
            'depth': 2
        },
        {
            'id': 'trace_5',
            'input': 'What is 6+6?',
            'output': '12',
            'logical_difficulty': 1,
            'depth': 1
        }
    ]


@pytest.fixture
def temp_manifest_file(sample_dag_manifest):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_dag_manifest, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    temp_path.unlink()


class TestDeterministicShuffling:
    """Tests for deterministic shuffling with fixed seed (T023)."""

    def test_shuffle_with_fixed_seed_produces_same_order(self, sample_dag_manifest):
        """Verify that shuffling with the same seed produces identical order."""
        generator = PromptGenerator()
        
        seed = 42
        shuffled1 = generator.shuffle_logical_random(sample_dag_manifest, seed)
        shuffled2 = generator.shuffle_logical_random(sample_dag_manifest, seed)
        
        # IDs should match in order
        ids1 = [ex['id'] for ex in shuffled1]
        ids2 = [ex['id'] for ex in shuffled2]
        
        assert ids1 == ids2, "Same seed should produce same shuffle order"

    def test_shuffle_with_different_seed_produces_different_order(self, sample_dag_manifest):
        """Verify that different seeds produce different orders (with high probability)."""
        generator = PromptGenerator()
        
        shuffled1 = generator.shuffle_logical_random(sample_dag_manifest, seed=42)
        shuffled2 = generator.shuffle_logical_random(sample_dag_manifest, seed=123)
        
        ids1 = [ex['id'] for ex in shuffled1]
        ids2 = [ex['id'] for ex in shuffled2]
        
        # Note: There's a small probability of collision, but it's extremely unlikely
        # For 5 elements, there are 120 permutations. Probability of collision is 1/120.
        assert ids1 != ids2 or len(set(ids1)) < 2, "Different seeds should typically produce different orders"

    def test_shuffle_preserves_all_elements(self, sample_dag_manifest):
        """Verify that shuffling preserves all elements."""
        generator = PromptGenerator()
        
        shuffled = generator.shuffle_logical_random(sample_dag_manifest, seed=42)
        
        original_ids = sorted([ex['id'] for ex in sample_dag_manifest])
        shuffled_ids = sorted([ex['id'] for ex in shuffled])
        
        assert original_ids == shuffled_ids, "Shuffling should preserve all elements"

    def test_shuffle_with_empty_list(self):
        """Verify that shuffling an empty list returns an empty list."""
        generator = PromptGenerator()
        
        shuffled = generator.shuffle_logical_random([], seed=42)
        
        assert shuffled == [], "Shuffling empty list should return empty list"

    def test_shuffle_with_single_element(self, sample_dag_manifest):
        """Verify that shuffling a single element list returns the same list."""
        generator = PromptGenerator()
        
        single = [sample_dag_manifest[0]]
        shuffled = generator.shuffle_logical_random(single, seed=42)
        
        assert len(shuffled) == 1
        assert shuffled[0]['id'] == single[0]['id']

    def test_shuffle_does_not_modify_original(self, sample_dag_manifest):
        """Verify that shuffling does not modify the original list."""
        generator = PromptGenerator()
        
        original_ids = [ex['id'] for ex in sample_dag_manifest]
        _ = generator.shuffle_logical_random(sample_dag_manifest, seed=42)
        current_ids = [ex['id'] for ex in sample_dag_manifest]
        
        assert original_ids == current_ids, "Original list should not be modified"

    def test_shuffle_with_large_seed_values(self, sample_dag_manifest):
        """Verify that large seed values work correctly."""
        generator = PromptGenerator()
        
        large_seed = 2**31 - 1
        shuffled = generator.shuffle_logical_random(sample_dag_manifest, seed=large_seed)
        
        assert len(shuffled) == len(sample_dag_manifest)
        assert [ex['id'] for ex in shuffled] != original_ids if len(set(original_ids)) > 1 else True

def test_load_manifest_from_file(temp_manifest_file, sample_dag_manifest):
    """Test loading manifest from file."""
    generator = PromptGenerator()
    
    loaded = generator.load_manifest(temp_manifest_file)
    
    assert len(loaded) == len(sample_dag_manifest)
    assert loaded[0]['id'] == sample_dag_manifest[0]['id']

def test_load_manifest_missing_file():
    """Test loading manifest from non-existent file."""
    generator = PromptGenerator()
    
    with pytest.raises(FileNotFoundError):
        generator.load_manifest(Path('/nonexistent/path.json'))

def test_sort_logical_ascending(temp_manifest_file):
    """Test logical ascending sort."""
    generator = PromptGenerator()
    examples = generator.load_manifest(temp_manifest_file)
    
    sorted_examples = generator.sort_logical_ascending(examples)
    
    depths = [ex['depth'] for ex in sorted_examples]
    assert depths == sorted(depths), "Should be sorted in ascending order"

def test_assemble_prompt():
    """Test prompt assembly."""
    generator = PromptGenerator()
    
    examples = [
        {'input': 'Q1', 'output': 'A1'},
        {'input': 'Q2', 'output': 'A2'}
    ]
    
    prompt = generator.assemble_prompt(examples)
    
    assert 'Q1' in prompt
    assert 'A1' in prompt
    assert 'Q2' in prompt
    assert 'A2' in prompt
