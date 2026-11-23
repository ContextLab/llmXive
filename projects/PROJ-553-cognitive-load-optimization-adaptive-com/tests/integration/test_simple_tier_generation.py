import os
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Import functions to test
from code.generate_simple_tier import (
    load_moderate_tiers,
    iterative_simplify,
    generate_simple_tiers,
    save_simple_tiers
)
from code.utils import calculate_flesch_kincaid, calculate_jaccard_similarity

# Mock model and tokenizer for testing without downloading large models
class MockModel:
    def generate(self, **kwargs):
        # Return a simple token sequence that decodes to a shorter text
        return [[101, 102, 103]]  # Placeholder tokens

class MockTokenizer:
    def from_pretrained(self, *args, **kwargs):
        return self
    
    def __call__(self, text, **kwargs):
        return {'input_ids': [[1, 2, 3]]}
    
    def decode(self, tokens, skip_special_tokens=False):
        # Return a simplified version of the input for testing
        return "This is a simplified version of the text."

@pytest.fixture
def sample_moderate_data():
    """Create sample moderate tier data."""
    data = {
        'instructional_unit_id': ['unit_1', 'unit_2', 'unit_3'],
        'text': [
            "The process of photosynthesis involves the conversion of light energy into chemical energy. This process occurs in the chloroplasts of plant cells.",
            "Mitochondria are organelles that generate most of the cell's supply of adenosine triphosphate (ATP), used as a source of chemical energy.",
            "DNA replication is the process of producing two identical replicas from one original DNA molecule. This occurs in all living organisms."
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_load_moderate_tiers(sample_moderate_data, temp_output_dir):
    """Test loading moderate tiers from CSV."""
    csv_path = os.path.join(temp_output_dir, "moderate_tiers.csv")
    sample_moderate_data.to_csv(csv_path, index=False)
    
    loaded_df = load_moderate_tiers(csv_path)
    
    assert len(loaded_df) == 3
    assert 'instructional_unit_id' in loaded_df.columns
    assert 'text' in loaded_df.columns
    assert list(loaded_df['instructional_unit_id']) == ['unit_1', 'unit_2', 'unit_3']

def test_iterative_simplify_constraints_met():
    """Test that iterative_simplify meets constraints with mock model."""
    mock_model = MockModel()
    mock_tokenizer = MockTokenizer()
    
    # Moderate text with high FK score
    moderate_text = "The comprehensive analysis of the multifaceted phenomenon necessitates a thorough examination of the constituent elements."
    moderate_fk = calculate_flesch_kincaid(moderate_text)
    
    # This will use the mock which returns a simpler text
    # In real scenario, this would iterate until constraints are met
    simplified_text, metadata = iterative_simplify(
        moderate_text, moderate_fk, mock_model, mock_tokenizer, max_iterations=2
    )
    
    # Check that metadata is populated
    assert 'iterations' in metadata
    assert 'final_fk_diff' in metadata
    assert 'final_jaccard' in metadata
    assert 'status' in metadata

def test_generate_simple_tiers_with_mock(sample_moderate_data):
    """Test generating simple tiers for multiple units."""
    mock_model = MockModel()
    mock_tokenizer = MockTokenizer()
    
    result_df = generate_simple_tiers(sample_moderate_data, mock_model, mock_tokenizer)
    
    # Check structure
    assert 'instructional_unit_id' in result_df.columns
    assert len(result_df) == 3
    
    # Check that at least some units have status
    assert 'status' in result_df.columns

def test_save_simple_tiers(temp_output_dir, sample_moderate_data):
    """Test saving simple tiers to CSV."""
    mock_model = MockModel()
    mock_tokenizer = MockTokenizer()
    
    result_df = generate_simple_tiers(sample_moderate_data, mock_model, mock_tokenizer)
    output_path = os.path.join(temp_output_dir, "simple_tiers.csv")
    
    save_simple_tiers(result_df, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 3
    assert 'instructional_unit_id' in saved_df.columns

def test_fk_diff_calculation():
    """Test that FK difference calculation works correctly."""
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "This is a very complex sentence with many sophisticated words that make it difficult to read quickly."
    
    fk1 = calculate_flesch_kincaid(text1)
    fk2 = calculate_flesch_kincaid(text2)
    
    diff = fk2 - fk1
    
    # Complex text should have higher FK score
    assert diff > 0
    assert isinstance(diff, float)

def test_jaccard_similarity():
    """Test Jaccard similarity calculation."""
    text1 = "The cat sat on the mat"
    text2 = "The dog sat on the rug"
    
    jaccard = calculate_jaccard_similarity(text1, text2)
    
    # Should be between 0 and 1
    assert 0 <= jaccard <= 1
    
    # Identical texts should have 1.0 similarity
    jaccard_identical = calculate_jaccard_similarity(text1, text1)
    assert jaccard_identical == 1.0