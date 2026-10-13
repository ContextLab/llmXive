import os
import yaml
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def test_setup_data_creates_state(tmp_path, monkeypatch):
    """
    Run the setup_data script and verify that:
    - The required directories exist.
    - ``project_state.yaml`` is created under ``data/``.
    - The YAML contains the expected keys.
    """
    # Import the main function from the script
    from src.data_pipeline.setup_data import main

    # Ensure a clean environment: remove any existing state file
    state_file = paths.data("project_state.yaml")
    if state_file.exists():
        state_file.unlink()

    # Run the setup routine
    main()

    # Check that the state file now exists
    assert state_file.exists(), "project_state.yaml was not created"

    # Load and inspect the YAML content
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)

    # Required top‑level keys
    required_keys = {"timestamp", "raw_checksums", "dataset_accessible", "geo_accession"}
    assert required_keys.issubset(state.keys()), f"Missing keys in state: {required_keys - set(state.keys())}"

    # raw_checksums should be a dict (may be empty if no raw files yet)
    assert isinstance(state["raw_checksums"], dict), "raw_checksums is not a dict"

    # dataset_accessible should be a boolean
    assert isinstance(state["dataset_accessible"], bool), "dataset_accessible is not a bool"

    # Verify that the required directories were created
    for dir_func in [paths.code, lambda: paths.data("raw"), lambda: paths.data("processed"), paths.figures, paths.results]:
        dir_path = dir_func()
        assert dir_path.is_dir(), f"Required directory missing: {dir_path}"