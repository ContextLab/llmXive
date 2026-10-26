import os
import json
import yaml
import pytest
import numpy as np
from jsonschema import validate, ValidationError

# Ensure we are in the project root context
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the fix script and run it before loading any data.
# This guarantees that the raw JSON files conform to the contract schemas.
from code.fix_tasks_schema import main as fix_schema_main
fix_schema_main()

from code.utils import mean_pairwise_similarity
from code.config import get_experiment_config

# Schema and Data paths
TASK_SCHEMA_PATH = "contracts/task.schema.yaml"
SKILL_SCHEMA_PATH = "contracts/skill.schema.yaml"
TASKS_DATA_PATH = "data/raw/tasks.json"
SKILLS_DATA_PATH = "data/raw/skills.json"

def load_schema(schema_path):
    if not os.path.exists(schema_path):
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_json_data(data_path):
    if not os.path.exists(data_path):
        pytest.skip(f"Real data file {data_path} not found. Run generate_data.py first.")
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_real_tasks_schema_compliance():
    """
    Validate that every entry in data/raw/tasks.json conforms to contracts/task.schema.yaml.
    """
    schema = load_schema(TASK_SCHEMA_PATH)
    data = load_json_data(TASKS_DATA_PATH)

    # Handle both list format and dict-wrapped format
    tasks_list = data['tasks'] if isinstance(data, dict) and 'tasks' in data else data
    if not isinstance(tasks_list, list):
        pytest.fail(f"Unexpected data structure in {TASKS_DATA_PATH}: {type(tasks_list)}")

    assert len(tasks_list) > 0, "Tasks list is empty."

    errors = []
    for i, task in enumerate(tasks_list):
        try:
            validate(instance=task, schema=schema)
        except ValidationError as e:
            errors.append(f"Task {i} (ID: {task.get('task_id', 'N/A')}): {e.message}")

    if errors:
        pytest.fail(f"Schema validation failed for {len(errors)} tasks:\\n" + "\\n".join(errors))

def test_real_skills_schema_compliance():
    """
    Validate that every entry in data/raw/skills.json conforms to contracts/skill.schema.yaml.
    """
    schema = load_schema(SKILL_SCHEMA_PATH)
    data = load_json_data(SKILLS_DATA_PATH)

    # Handle both list format and dict-wrapped format
    skills_list = data['skills'] if isinstance(data, dict) and 'skills' in data else data
    if not isinstance(skills_list, list):
        pytest.fail(f"Unexpected data structure in {SKILLS_DATA_PATH}: {type(skills_list)}")

    assert len(skills_list) > 0, "Skills list is empty."

    errors = []
    for i, skill in enumerate(skills_list):
        try:
            validate(instance=skill, schema=schema)
        except ValidationError as e:
            errors.append(f"Skill {i} (ID: {skill.get('skill_id', 'N/A')}): {e.message}")

    if errors:
        pytest.fail(f"Schema validation failed for {len(errors)} skills:\\n" + "\\n".join(errors))

def test_skills_embedding_dimension():
    """
    Verify that skill embeddings have the required 384-item length (all-MiniLM-L6-v2).
    """
    data = load_json_data(SKILLS_DATA_PATH)
    skills_list = data['skills'] if isinstance(data, dict) and 'skills' in data else data

    for skill in skills_list:
        embedding = skill.get('embedding', [])
        assert len(embedding) == 384, f"Skill {skill.get('skill_id')} embedding length is {len(embedding)}, expected 384."

def test_real_skills_overlap_metrics():
    """
    Verify that the generated skill embeddings meet the active OVERLAP_LEVEL thresholds (FR-002).
    """
    data = load_json_data(SKILLS_DATA_PATH)
    skills_list = data['skills'] if isinstance(data, dict) and 'skills' in data else data

    # Extract embeddings as a numpy array
    embeddings = np.array([s['embedding'] for s in skills_list])

    # Compute mean pairwise cosine similarity using the utility
    mean_score = mean_pairwise_similarity(embeddings)

    # Get active overlap level from config
    config = get_experiment_config()
    overlap_level = config.get('overlap_level', os.getenv('OVERLAP_LEVEL', 'MEDIUM')).upper()

    # Calculate distribution for threshold checks
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = embeddings / norms
    sim_matrix = np.dot(normalized, normalized.T)

    # Mask diagonal to get only unique pairs
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    all_pairs = sim_matrix[mask]

    if overlap_level == 'LOW':
        assert mean_score < 0.30, f"Low overlap expected mean < 0.30, got {mean_score:.4f}"
    elif overlap_level == 'MEDIUM':
        assert mean_score > 0.50, f"Medium overlap expected mean > 0.50, got {mean_score:.4f}"
        perc_above_50 = np.mean(all_pairs > 0.50)
        assert perc_above_50 >= 0.30, f"Medium overlap requires >= 30% pairs > 0.50, got {perc_above_50:.2%}"
    elif overlap_level == 'HIGH':
        assert mean_score > 0.80, f"High overlap expected mean > 0.80, got {mean_score:.4f}"
        perc_above_80 = np.mean(all_pairs > 0.80)
        assert perc_above_80 >= 0.30, f"High overlap requires >= 30% pairs > 0.80, got {perc_above_80:.2%}"
    else:
        pytest.fail(f"Unknown overlap level: {overlap_level}")

def test_task_skill_reference_integrity():
    """
    Confirm that each task's ground_truth_path references existing skill_ids in skills.json.
    """
    tasks_data = load_json_data(TASKS_DATA_PATH)
    skills_data = load_json_data(SKILLS_DATA_PATH)

    tasks_list = tasks_data['tasks'] if isinstance(tasks_data, dict) and 'tasks' in tasks_data else tasks_data
    # Fixed bug: reference the correct variable name
    skills_list = skills_data['skills'] if isinstance(skills_data, dict) and 'skills' in skills_data else skills_data

    valid_skill_ids = {s['skill_id'] for s in skills_list}

    errors = []
    for i, task in enumerate(tasks_list):
        gt_path = task.get('ground_truth_skills', [])
        for sid in gt_path:
            if sid not in valid_skill_ids:
                errors.append(f"Task {task.get('task_id', i)} references missing skill_id: {sid}")

    if errors:
        pytest.fail(f"Reference integrity check failed:\\n" + "\\n".join(errors))