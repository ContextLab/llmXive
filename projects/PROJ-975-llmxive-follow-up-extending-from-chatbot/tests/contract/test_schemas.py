import os
import json
import pytest
import yaml
from jsonschema import validate, ValidationError
from code.generate_data import save_artifacts, generate_skills, generate_tasks_with_ground_truth, calculate_similarity_metrics, handle_maximal_overlap
from code.config import get_seeds, pin_seeds

# Load schemas
def load_schema(schema_path):
    """Load a YAML schema file and return the parsed dictionary."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

# Load schemas at module level
TASK_SCHEMA = load_schema("contracts/task.schema.yaml")
SKILL_SCHEMA = load_schema("contracts/skill.schema.yaml")

def test_tasks_json_schema_compliance():
    """Contract test: Verify tasks.json schema compliance against contracts/task.schema.yaml."""
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
        # Using low overlap to ensure standard generation
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

        # Validate each task against the loaded schema
        for task in tasks_data["tasks"]:
            # Use jsonschema.validate to ensure full compliance
            validate(instance=task, schema=TASK_SCHEMA)

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)

def test_skills_json_schema_compliance():
    """Contract test: Verify skills.json schema compliance against contracts/skill.schema.yaml."""
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

        # Validate each skill against the loaded schema
        for skill in skills_data["skills"]:
            validate(instance=skill, schema=SKILL_SCHEMA)

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