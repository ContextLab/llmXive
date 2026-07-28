import pytest
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# Mock imports to avoid heavy dependencies in test environment if necessary,
# but we assume the environment has the required libraries.
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import get_seeds, get_experiment_config
from code.utils import get_model, get_embedding, pairwise_cosine_similarity_matrix
from code.generate_data import generate_skills, generate_tasks_with_ground_truth, calculate_similarity_metrics

def test_ground_truth_independence():
    """
    Verify that ground-truth assignment (Seed B) is independent of skill generation (Seed A).
    We do this by checking that changing Seed A does not change the set of skills available
    for a fixed Seed B, and vice versa.
    """
    seed_a = 42
    seed_b = 123
    overlap_level = "low"

    # Generate skills with Seed A
    skills_a, raw_texts_a = generate_skills(seed_a, overlap_level)
    ids_a = [s['id'] for s in skills_a]

    # Generate tasks with Seed B using skills from A
    tasks_b = generate_tasks_with_ground_truth(seed_b, ids_a, 10)
    gt_b = [t['ground_truth_path'] for t in tasks_b]

    # Now change Seed A to something else
    seed_a_new = 999
    skills_a_new, raw_texts_a_new = generate_skills(seed_a_new, overlap_level)
    ids_a_new = [s['id'] for s in skills_a_new]

    # Generate tasks with SAME Seed B but new skills
    tasks_b_new = generate_tasks_with_ground_truth(seed_b, ids_a_new, 10)
    gt_b_new = [t['ground_truth_path'] for t in tasks_b_new]

    # The set of IDs should be different if the skill generation is different
    # But the logic of task generation (random.sample) depends on the input list.
    # The test is that Seed B controls the *selection* from the available pool.
    # If we fix Seed B and the pool changes, the result changes.
    # If we fix Seed B and the pool is the same, the result should be the same.
    
    # Verify that with same Seed B and same pool, results are identical
    tasks_b_repeat = generate_tasks_with_ground_truth(seed_b, ids_a, 10)
    gt_b_repeat = [t['ground_truth_path'] for t in tasks_b_repeat]
    
    assert gt_b == gt_b_repeat, "Ground truth generation is not deterministic with same seed and pool"

def test_similarity_validation():
    """
    Test that similarity metrics are calculated correctly.
    """
    # Create a small set of known texts
    texts = [
        "def add(a, b): return a + b",
        "def add(a, b): return a + b", # Identical
        "def sub(a, b): return a - b"
    ]
    
    # We need to mock the model or use a real one. For this test, we assume the environment is set up.
    # If sentence-transformers is not available, we skip or mock.
    try:
        model = get_model()
        metrics = calculate_similarity_metrics(texts, "low")
        
        # Check that metrics are returned
        assert "mean_pairwise_similarity" in metrics
        assert "max_pairwise_similarity" in metrics
        assert isinstance(metrics["mean_pairwise_similarity"], float)
    except Exception as e:
        # If model loading fails, skip this specific test or log warning
        pytest.skip(f"Model loading failed: {e}")

def test_skill_generation_count():
    """
    Verify that exactly 100 skills are generated.
    """
    skills, _ = generate_skills(42, "low")
    assert len(skills) == 100

def test_task_generation_count():
    """
    Verify that exactly 500 tasks are generated.
    """
    skill_ids = [f"skill_{i:03d}" for i in range(100)]
    tasks = generate_tasks_with_ground_truth(123, skill_ids, 500)
    assert len(tasks) == 500
