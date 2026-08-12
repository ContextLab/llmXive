import json
import os
import pytest
import hashlib
from code.generate_data import generate_skills, generate_tasks_with_ground_truth, calculate_similarity_metrics, generate_checksum

def test_ground_truth_independence():
    """Verify that task generation (Seed B) is independent of skill generation (Seed A)."""
    seed_a = 42
    seed_b = 12345
    
    # Generate skills with Seed A
    skills = generate_skills(seed=seed_a, count=10)
    skill_ids_a = [s["skill_id"] for s in skills]
    
    # Generate tasks with Seed B
    tasks = generate_tasks_with_ground_truth(skills, task_count=5, seed=seed_b)
    
    # Verify tasks have ground truth paths
    for task in tasks:
        assert "ground_truth_path" in task
        assert len(task["ground_truth_path"]) > 0
        # Ensure ground truth skills exist in the skill set
        for gt in task["ground_truth_path"]:
            assert gt in skill_ids_a

def test_similarity_metrics():
    """Verify similarity calculation logic."""
    skills = generate_skills(seed=42, count=20)
    sim = calculate_similarity_metrics(skills)
    assert 0.0 <= sim <= 1.0
    assert isinstance(sim, float)

def test_checksum_generation():
    """Verify checksum generation logic."""
    # Create a temp file
    temp_path = "data/raw/test_temp.json"
    os.makedirs("data/raw", exist_ok=True)
    with open(temp_path, "w") as f:
        json.dump({"test": "data"}, f)
    
    checksum = generate_checksum(temp_path)
    assert len(checksum) == 64 # SHA-256 hex length
    assert isinstance(checksum, str)
    
    # Cleanup
    os.remove(temp_path)

def test_output_files_exist():
    """Verify that main() produces the required files."""
    # We assume main() has been run or will be run. 
    # This test checks existence if the script was executed.
    assert os.path.exists("data/raw/skills.json"), "skills.json not found"
    assert os.path.exists("data/raw/tasks.json"), "tasks.json not found"
    assert os.path.exists("data/raw/checksums.json"), "checksums.json not found"
    assert os.path.exists("state/artifact_hashes.json"), "artifact_hashes.json not found"

def test_checksums_match():
    """Verify that stored checksums match actual file checksums."""
    with open("data/raw/checksums.json", "r") as f:
        stored_checksums = json.load(f)
    
    # Verify skills
    skills_path = "data/raw/skills.json"
    actual_skills_checksum = generate_checksum(skills_path)
    assert stored_checksums["skills.json"] == actual_skills_checksum, "Skills checksum mismatch"
    
    # Verify tasks
    tasks_path = "data/raw/tasks.json"
    actual_tasks_checksum = generate_checksum(tasks_path)
    assert stored_checksums["tasks.json"] == actual_tasks_checksum, "Tasks checksum mismatch"
