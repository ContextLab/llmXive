import os
import json
import pytest
import numpy as np
from code.generate_data import (
    generate_skills, 
    calculate_similarity_metrics, 
    generate_tasks_with_ground_truth,
    handle_maximal_overlap,
    generate_checksum,
    save_artifacts
)
from code.config import get_seeds, pin_seeds

def test_generate_skills_deterministic():
    """Test that skill generation is deterministic with same seed."""
    seed = 42
    pin_seeds(seed)
    skills1, _ = generate_skills(seed, "low")
    
    pin_seeds(seed)
    skills2, _ = generate_skills(seed, "low")
    
    assert len(skills1) == len(skills2)
    assert skills1[0]["skill_id"] == skills2[0]["skill_id"]
    assert skills1[0]["description"] == skills2[0]["description"]

def test_similarity_metrics_calculation():
    """Test that similarity metrics are calculated correctly."""
    # Create dummy embeddings
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    metrics = calculate_similarity_metrics(embeddings)
    
    assert "mean_pairwise_similarity" in metrics
    assert "pairwise_matrix" in metrics
    assert metrics["mean_pairwise_similarity"] == pytest.approx(0.0, abs=1e-5)
    assert len(metrics["pairwise_matrix"]) == 3

def test_ground_truth_independence():
    """Test that task ground truth assignment uses distinct seed (Seed B)."""
    skill_ids = ["skill_001", "skill_002", "skill_003"]
    
    # Generate with Seed B = 100
    tasks1 = generate_tasks_with_ground_truth(skill_ids, 100, 5)
    
    # Generate with Seed B = 200
    tasks2 = generate_tasks_with_ground_truth(skill_ids, 200, 5)
    
    # The ground truth paths should differ
    # (At least one task should have a different ground_truth_path)
    different = False
    for t1, t2 in zip(tasks1, tasks2):
        if t1["ground_truth_path"] != t2["ground_truth_path"]:
            different = True
            break
    
    assert different, "Ground truth paths should differ when using different seeds"

def test_maximal_overlap_handling():
    """Test handling of maximal overlap (mean_sim >= 0.95)."""
    high_sim = 0.96
    tasks = [{"task_id": "task_001"}]
    
    metadata = handle_maximal_overlap(high_sim, tasks)
    
    assert metadata["maximal_overlap_detected"] is True
    assert metadata["tie_breaking_applied"] is True

def test_checksum_generation():
    """Test that checksum generation produces valid SHA-256 hashes."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"test": "data"}, f)
        temp_path = f.name
    
    try:
        checksum = generate_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_save_artifacts_creates_files():
    """Test that save_artifacts creates the required files."""
    import tempfile
    import shutil
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("state", exist_ok=True)
        
        skills = [{"skill_id": "s1", "description": "Test"}]
        tasks = [{"task_id": "t1", "ground_truth_path": ["s1"]}]
        metadata = {"maximal_overlap_detected": False}
        
        save_artifacts(skills, tasks, metadata, "low", 42, 123)
        
        # Verify files exist
        assert os.path.exists("data/raw/skills.json")
        assert os.path.exists("data/raw/tasks.json")
        assert os.path.exists("data/raw/checksums.json")
        assert os.path.exists("state/artifact_hashes.json")
        
        # Verify content structure
        with open("data/raw/skills.json") as f:
            skills_data = json.load(f)
            assert "metadata" in skills_data
            assert "skills" in skills_data
            assert skills_data["metadata"]["overlap_level"] == "low"
        
        with open("data/raw/tasks.json") as f:
            tasks_data = json.load(f)
            assert "metadata" in tasks_data
            assert "tasks" in tasks_data
            assert "maximal_overlap_detected" in tasks_data["metadata"]
        
        with open("data/raw/checksums.json") as f:
            checksums = json.load(f)
            assert "skills.json" in checksums
            assert "tasks.json" in checksums
            assert len(checksums["skills.json"]) == 64
            assert len(checksums["tasks.json"]) == 64
    
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)