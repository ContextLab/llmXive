import json
import pathlib
import pytest
import numpy as np
from jsonschema import validate
from llmxive_toolkit import paths

def load_yaml_schema(name):
    import yaml
    path = paths.path("contracts", f"{name}.schema.yaml")
    if not path.exists():
        pytest.skip(f"Schema {path} not found.")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def test_counts():
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    
    if not tasks_path.exists() or not skills_path.exists():
        pytest.skip("Data files not found. Run generate_data.py first.")

    with open(tasks_path, 'r') as f:
        tasks = json.load(f)['tasks']
    with open(skills_path, 'r') as f:
        skills = json.load(f)['skills']
    
    assert len(tasks) == 500
    assert len(skills) == 100

def test_schema_compliance():
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    
    if not tasks_path.exists() or not skills_path.exists():
        pytest.skip("Data files not found.")

    with open(tasks_path, 'r') as f:
        tasks = json.load(f)['tasks']
    with open(skills_path, 'r') as f:
        skills = json.load(f)['skills']

    task_schema = load_yaml_schema("task")
    skill_schema = load_yaml_schema("skill")

    for t in tasks:
        validate(instance=t, schema=task_schema)
    for s in skills:
        validate(instance=s, schema=skill_schema)

def test_checksum_integrity():
    checksums_path = paths.data("raw", "checksums.json")
    if not checksums_path.exists():
        pytest.skip("Checksum file not found.")
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    import hashlib
    def get_sha(p):
        sha = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    assert checksums["tasks_json_sha256"] == get_sha(paths.data("raw", "tasks.json"))
    assert checksums["skills_json_sha256"] == get_sha(paths.data("raw", "skills.json"))

def test_overlap_logic():
    # This test verifies the logic of the generator via the produced data
    skills_path = paths.data("raw", "skills.json")
    if not skills_path.exists():
        pytest.skip("Skills file not found.")

    with open(skills_path, 'r') as f:
        skills = json.load(f)['skills']
    
    embeddings = np.array([s['embedding'] for s in skills])
    sim_matrix = embeddings @ embeddings.T
    mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
    mean_sim = sim_matrix[mask].mean()
    
    # Since generate_data.py was run with --overlap high in artifacts, 
    # we check for high overlap thresholds.
    # In a real CI, the overlap level would be parameterized.
    # For this specific artifact run, we expect HIGH.
    assert mean_sim > 0.80, f"Expected high overlap (>0.8), got {mean_sim:.4f}"