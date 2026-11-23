import pytest
import json
import csv
import tempfile
import os
from pathlib import Path
import numpy as np

# Mock the local imports to avoid dependency on full project setup for unit tests
# We will test the logic by patching or using standalone functions if exposed
# Since validate_ood.py has main logic in functions, we can import them directly
# but we need to handle the logger and config dependencies.

# For this unit test, we will test the core logic functions:
# compute_cosine_similarity, and the flow of validate_ood_prompts with mocks.

from code.data.validate_ood import compute_cosine_similarity, compute_embeddings, load_prompts

class TestComputeCosineSimilarity:
    def test_identical_vectors(self):
        # If vectors are identical, similarity should be 1.0
        ood = np.array([[1.0, 0.0], [0.0, 1.0]])
        centroid = np.array([1.0, 0.0])
        sims = compute_cosine_similarity(ood, centroid)
        assert np.isclose(sims[0], 1.0)
        assert np.isclose(sims[1], 0.0)

    def test_opposite_vectors(self):
        # If vectors are opposite, similarity should be -1.0
        ood = np.array([[-1.0, 0.0]])
        centroid = np.array([1.0, 0.0])
        sims = compute_cosine_similarity(ood, centroid)
        assert np.isclose(sims[0], -1.0)

    def test_threshold_check(self):
        # Test case where similarity > 0.3
        ood = np.array([[0.5, 0.5]]) # Normalized: ~[0.707, 0.707]
        centroid = np.array([0.707, 0.707]) # Normalized
        # Dot product ~ 0.5 + 0.5 = 1.0 (if perfectly aligned)
        # Let's create a simpler case
        ood = np.array([[0.8, 0.6]]) # Norm = 1.0
        centroid = np.array([1.0, 0.0]) # Norm = 1.0
        sims = compute_cosine_similarity(ood, centroid)
        # 0.8 * 1 + 0.6 * 0 = 0.8
        assert sims[0] > 0.3

class TestLoadPrompts:
    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['prompt', 'id'])
            writer.writeheader()
            writer.writerow({'prompt': 'test prompt 1', 'id': 1})
            writer.writerow({'prompt': 'test prompt 2', 'id': 2})
            temp_path = f.name

        try:
            prompts = load_prompts(Path(temp_path))
            assert len(prompts) == 2
            assert prompts[0] == 'test prompt 1'
            assert prompts[1] == 'test prompt 2'
        finally:
            os.unlink(temp_path)

    def test_load_missing_column(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['text', 'id'])
            writer.writeheader()
            writer.writerow({'text': 'test', 'id': 1})
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_prompts(Path(temp_path))
        finally:
            os.unlink(temp_path)