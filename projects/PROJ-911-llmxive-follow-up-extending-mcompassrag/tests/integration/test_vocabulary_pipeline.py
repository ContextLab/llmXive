import pytest
import json
import os
from pathlib import Path

from code.vocabulary_builder import run_pipeline
from code.config import PROCESSED_DIR


class TestVocabularyPipelineIntegration:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Ensure the processed directory exists
        Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
        yield
        # Optional: cleanup after test if needed, but usually we want to keep artifacts for verification
        # if os.path.exists(output_file):
        #     os.remove(output_file)

    def test_run_pipeline_creates_file(self, tmp_path):
        # Temporarily override PROCESSED_DIR for this test to use tmp_path
        # However, since run_pipeline uses the constant from config, we mock it or use a specific file name
        # A better approach for integration test is to run it and check if the file exists in the expected location
        # or mock the output path. Here we will run it and check the file exists in PROCESSED_DIR
        
        # Mock corpus
        corpus = [
            "Machine learning is a subset of artificial intelligence.",
            "Deep learning uses neural networks with many layers.",
            "Natural language processing helps computers understand human language.",
            "Computer vision enables machines to interpret visual data."
        ]
        
        output_filename = "test_fixed_vocab.json"
        
        # Run the pipeline
        output_path = run_pipeline(corpus, output_filename=output_filename)
        
        # Verify the file exists
        assert os.path.exists(output_path), f"Output file {output_path} was not created."
        
        # Verify the content is valid JSON
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Vocabulary should be saved as a list."
        assert len(data) > 0, "Vocabulary should not be empty."
        
        # Verify it's sorted (as per implementation)
        assert data == sorted(data), "Vocabulary list should be sorted."

    def test_pipeline_handles_small_corpus(self):
        corpus = ["one two three"]
        output_filename = "test_small_vocab.json"
        output_path = run_pipeline(corpus, output_filename=output_filename)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        # Might be empty if min_df filters out everything, but file should exist
        assert isinstance(data, list)
