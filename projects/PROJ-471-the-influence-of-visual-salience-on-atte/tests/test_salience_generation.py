import json
import pathlib

import cv2
import numpy as np
import pytest
import yaml
from jsonschema import validate, ValidationError

# Import the script's main function
from code.salience.generate_maps import main as generate_maps_main

# Helper to load the schema
def load_schema():
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "salience.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def run_generation(tmp_path_factory):
    """
    Execute the salience map generation script once for the test module.
    Returns the root project path for later checks.
    """
    # Ensure we run from project root
    project_root = pathlib.Path(__file__).resolve().parents[2]
    # Change cwd to project root so llmxive paths work correctly
    import os
    cwd = os.getcwd()
    os.chdir(project_root)
    try:
        exit_code = generate_maps_main()
        assert exit_code == 0, f"generate_maps exited with code {exit_code}"
    finally:
        os.chdir(cwd)
    return project_root

def test_salience_maps_exist_and_match_resolution(run_generation):
    """
    Verify that a .npy file exists for each stimulus image and that its
    dimensions match the source image resolution.
    """
    project_root = run_generation
    raw_dir = project_root / "data" / "raw" / "ds003123" / "stimuli"
    maps_dir = project_root / "data" / "interim" / "salience_maps"

    for img_path in raw_dir.glob("*.png"):
        stimulus_id = img_path.stem
        map_path = maps_dir / f"{stimulus_id}.npy"
        assert map_path.is_file(), f"Salience map missing for {stimulus_id}"

        # Load both image and map to compare dimensions
        img = cv2.imread(str(img_path))
        assert img is not None, f"Failed to read source image {img_path}"
        img_h, img_w = img.shape[:2]

        sal_map = np.load(str(map_path))
        assert sal_map.shape == (img_h, img_w), (
            f"Resolution mismatch for {stimulus_id}: "
            f"image ({img_h},{img_w}) vs map {sal_map.shape}"
        )

def test_metadata_schema_and_content(run_generation):
    """
    Validate that the generated metadata JSON conforms to the contract
    and that each entry records correct information.
    """
    project_root = run_generation
    metadata_path = project_root / "data" / "interim" / "salience_metadata.json"
    assert metadata_path.is_file(), "salience_metadata.json not found"

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Basic structure checks
    assert isinstance(metadata, list), "Metadata should be a list of entries"
    assert len(metadata) > 0, "Metadata list is empty"

    schema = load_schema()

    for entry in metadata:
        # Validate against JSON schema
        try:
            validate(instance=entry, schema=schema)
        except ValidationError as ve:
            pytest.fail(f"Metadata entry failed schema validation: {ve}")

        # Ensure required fields are present and sensible
        assert entry["stimulus_id"], "stimulus_id is empty"
        assert entry["map_path"], "map_path is empty"
        res = entry["resolution"]
        assert res["height"] >= 1 and res["width"] >= 1, "Invalid resolution values"

        if entry["status"] == "failed":
            assert entry["excluded_reason"] is not None, "Failed entry missing excluded_reason"
        else:
            assert entry["excluded_reason"] is None, "Successful entry should have null excluded_reason"

def test_no_cuda_errors_present(run_generation, caplog):
    """
    Ensure that the script did not encounter any CUDA‑related errors.
    """
    # The logger from the script writes to the standard logger;
    # we capture log records via caplog.
    for record in caplog.records:
        if "CUDA" in record.message:
            pytest.fail(f"Unexpected CUDA error logged: {record.message}")