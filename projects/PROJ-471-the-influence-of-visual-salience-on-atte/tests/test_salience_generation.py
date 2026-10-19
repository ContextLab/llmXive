import json
import pathlib
import numpy as np
import pytest
import yaml
import cv2
from jsonschema import validate, ValidationError
from code.salience.generate_maps import main as generate_maps_main

def load_schema():
    # Path relative to test file: tests/test_salience_generation.py -> contracts/salience.schema.yaml
    # Note: Using a robust path resolution to find the schema
    project_root = pathlib.Path(__file__).resolve().parents[2]
    schema_path = project_root / "contracts" / "salience.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def run_generation():
    """
    Run the generation script and return the project root.
    """
    import os
    project_root = pathlib.Path(__file__).resolve().parents[2]
    cwd = os.getcwd()
    os.chdir(project_root)
    try:
        exit_code = generate_maps_main()
        assert exit_code == 0, f"generate_maps exited with code {exit_code}"
    finally:
        os.chdir(cwd)
    return project_root

def test_salience_outputs_exist(run_generation):
    """
    Verify that .npy maps and the metadata JSON are produced.
    """
    project_root = run_generation
    metadata_path = project_root / "data" / "interim" / "salience_metadata.json"
    maps_dir = project_root / "data" / "interim" / "salience_maps"
    
    assert metadata_path.is_file(), "salience_metadata.json was not created"
    assert maps_dir.is_dir(), "salience_maps directory was not created"

def test_metadata_schema_compliance(run_generation):
    """
    Validate salience_metadata.json against the YAML schema.
    """
    project_root = run_generation
    metadata_path = project_root / "data" / "interim" / "salience_metadata.json"
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    assert isinstance(metadata, list), "Metadata should be a list"
    schema = load_schema()
    
    for entry in metadata:
        try:
            validate(instance=entry, schema=schema)
        except ValidationError as ve:
            pytest.fail(f"Schema validation failed for entry {entry.get('stimulus_id')}: {ve}")

def test_map_resolutions_match_images(run_generation):
    """
    Ensure each .npy map matches the dimensions of its source image.
    """
    project_root = run_generation
    raw_dir = project_root / "data" / "raw" / "ds003123" / "stimuli"
    maps_dir = project_root / "data" / "interim" / "salience_maps"
    
    # Only check images that were actually processed (success)
    with open(project_root / "data" / "interim" / "salience_metadata.json", "r") as f:
        metadata = json.load(f)
    
    success_ids = [e["stimulus_id"] for e in metadata if e["status"] == "success"]
    
    for sid in success_ids:
        img_path = next(raw_dir.glob(f"{sid}.*"), None)
        if img_path is None:
            continue
        
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        
        map_path = maps_dir / f"{sid}.npy"
        assert map_path.is_file(), f"Map missing for {sid}"
        
        sal_map = np.load(str(map_path))
        assert sal_map.shape == (h, w), f"Resolution mismatch for {sid}: img({h},{w}) vs map{sal_map.shape}"

def test_error_log_exists(run_generation):
    """
    Verify that the error log file is created.
    """
    project_root = run_generation
    error_log = project_root / "logs" / "salience_errors.log"
    # The file should exist even if empty, provided the logger was initialized
    assert error_log.is_file(), "logs/salience_errors.log was not created"