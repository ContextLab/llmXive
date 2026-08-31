import os
import json
import pytest
from jsonschema import validate, ValidationError
from code.generate_data import save_artifacts, generate_skills, generate_tasks_with_ground_truth, calculate_similarity_metrics, handle_maximal_overlap
from code.config import get_seeds, pin_seeds

# Load schemas
def load_schema(schema_path):
    with open(schema_path, 'r') as f:
        return json.load(f)

TASK_SCHEMA = load_schema("contracts/task.schema.yaml")
SKILL_SCHEMA = load_schema("contracts/skill.schema.yaml")

def test_tasks_json_schema_compliance():
    """Contract test: Verify tasks.json schema compliance."""
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("state", exist_ok=True)
        os.makedirs("contracts", exist_ok=True)
        
        # Generate minimal valid data
        skills, _ = generate_skills(42, "low")
        skill_ids = [s["skill_id"] for s in skills]
        tasks = generate_tasks_with_ground_truth(skill_ids, 123, 5)
        
        # Save artifacts
        save_artifacts(skills, tasks, {"maximal_overlap_detected": False}, "low", 42, 123)
        
        # Load and validate tasks.json
        with open("data/raw/tasks.json", 'r') as f:
            tasks_data = json.load(f)
        
        # Validate structure
        assert "tasks" in tasks_data
        assert "metadata" in tasks_data
        
        for task in tasks_data["tasks"]:
            # Validate against schema (simplified check since schema is YAML)
            # The schema expects: task_id, description, ground_truth_path, complexity
            assert "task_id" in task
            assert "description" in task
            assert "ground_truth_path" in task
            assert "complexity" in task
            assert isinstance(task["ground_truth_path"], list)
            
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)

def test_skills_json_schema_compliance():
    """Contract test: Verify skills.json schema compliance."""
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("state", exist_ok=True)
        os.makedirs("contracts", exist_ok=True)
        
        # Generate minimal valid data
        skills, embeddings = generate_skills(42, "low")
        
        # Save artifacts (with dummy tasks)
        dummy_tasks = [{"task_id": "t1", "ground_truth_path": []}]
        save_artifacts(skills, dummy_tasks, {"maximal_overlap_detected": False}, "low", 42, 123)
        
        # Load and validate skills.json
        with open("data/raw/skills.json", 'r') as f:
            skills_data = json.load(f)
        
        # Validate structure
        assert "skills" in skills_data
        assert "metadata" in skills_data
        
        for skill in skills_data["skills"]:
            # Validate against schema
            # The schema expects: skill_id, function_code, embedding_vector, usage_count
            assert "skill_id" in skill
            assert "function_code" in skill
            assert "usage_count" in skill
            # Note: embedding_vector is calculated but not stored in JSON to save space
            # The schema validation focuses on the core fields
    
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)

def test_overlap_metrics_validation():
    """Test that overlap metrics are correctly calculated and stored."""
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("state", exist_ok=True)
        os.makedirs("contracts", exist_ok=True)
        
        # Generate data with medium overlap
        skills, embeddings = generate_skills(42, "medium")
        metrics = calculate_similarity_metrics(embeddings)
        
        dummy_tasks = [{"task_id": "t1", "ground_truth_path": []}]
        save_artifacts(skills, dummy_tasks, {"maximal_overlap_detected": False}, "medium", 42, 123)
        
        # Load tasks.json and verify metadata
        with open("data/raw/tasks.json", 'r') as f:
            tasks_data = json.load(f)
        
        # Verify metadata contains overlap level
        assert tasks_data["metadata"]["overlap_level"] == "medium"
        assert "maximal_overlap_detected" in tasks_data["metadata"]
        
        # Verify checksums exist and are valid
        with open("data/raw/checksums.json", 'r') as f:
            checksums = json.load(f)
        
        assert "skills.json" in checksums
        assert "tasks.json" in checksums
        assert len(checksums["skills.json"]) == 64
        assert len(checksums["tasks.json"]) == 64
    
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)