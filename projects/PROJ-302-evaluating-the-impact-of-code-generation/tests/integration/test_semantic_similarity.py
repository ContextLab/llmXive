import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from feature_extraction.semantic_similarity import (
    load_model_and_tokenizer,
    get_embeddings_batch,
    calculate_similarity,
    extract_semantic_similarity_scores,
    process_dataset
)

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'snippet_id': [1, 2, 3],
        'code_snippet': [
            'def hello():\n    print("Hello")',
            'def world():\n    print("World")',
            'def test():\n    assert True'
        ],
        'author_type': ['human', 'llm-like', 'human']
    })

@pytest.fixture
def model_tokenizer():
    # This might be slow to load in CI, but necessary for real test
    # In a real CI, we might mock this, but the requirement is real data/code
    return load_model_and_tokenizer()

def test_load_model(model_tokenizer):
    model, tokenizer = model_tokenizer
    assert model is not None
    assert tokenizer is not None

def test_get_embeddings_batch(model_tokenizer, sample_dataframe):
    model, tokenizer = model_tokenizer
    snippets = sample_dataframe['code_snippet'].tolist()
    embeddings = get_embeddings_batch(snippets, model, tokenizer, batch_size=2)
    assert embeddings.shape == (3, 768)  # CodeBERT hidden size is 768
    assert isinstance(embeddings, np.ndarray)

def test_calculate_similarity(model_tokenizer, sample_dataframe):
    model, tokenizer = model_tokenizer
    snippets = sample_dataframe['code_snippet'].tolist()
    embeddings = get_embeddings_batch(snippets, model, tokenizer, batch_size=2)
    indices = [(0, 1), (1, 2)]
    sims = calculate_similarity(embeddings, indices)
    assert len(sims) == 2
    assert all(-1.0 <= s <= 1.0 for s in sims)

def test_extract_semantic_similarity_scores(model_tokenizer, sample_dataframe):
    model, tokenizer = model_tokenizer
    result_df = extract_semantic_similarity_scores(sample_dataframe, model, tokenizer)
    assert 'semantic_similarity_score' in result_df.columns
    assert len(result_df) == 3
    # Scores should be between -1 and 1
    assert all(-1.0 <= s <= 1.0 for s in result_df['semantic_similarity_score'])

def test_process_dataset(model_tokenizer, sample_dataframe):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.parquet")
        output_path = os.path.join(tmpdir, "output.parquet")
        
        sample_dataframe.to_parquet(input_path)
        
        # We need to pass the model/tokenizer to the function or modify process_dataset
        # Since process_dataset loads the model internally, we can't easily inject it here
        # without refactoring. We will trust the integration test of the full pipeline.
        # Instead, we test the specific functions that process_dataset calls.
        pass

def test_full_pipeline_integration(sample_dataframe):
    """
    Test the full pipeline end-to-end with a small sample.
    This ensures the script actually writes the file as required.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.parquet")
        output_path = os.path.join(tmpdir, "output.parquet")
        
        sample_dataframe.to_parquet(input_path)
        
        # This will load the model and run the computation
        # It might take a few seconds
        process_dataset(input_path, output_path)
        
        assert os.path.exists(output_path)
        result_df = pd.read_parquet(output_path)
        assert 'semantic_similarity_score' in result_df.columns
        assert len(result_df) == len(sample_dataframe)
        # Verify the output matches the input rows
        assert list(result_df['snippet_id']) == list(sample_dataframe['snippet_id'])