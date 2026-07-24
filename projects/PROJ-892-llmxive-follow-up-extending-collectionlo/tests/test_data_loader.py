import os
import tempfile
import shutil
from pathlib import Path
import yaml

# Mock the environment to avoid actual downloads in unit tests
# We test the logic of registration and hashing without network calls

def test_compute_sha256():
    from code.data_loader import compute_sha256
    import hashlib

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)

    try:
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        actual_hash = compute_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_register_downloaded_artifact():
    from code.data_loader import register_downloaded_artifact, load_artifacts_state, save_artifacts_state, PROJECT_ROOT

    # Create a temp state file to avoid polluting real state
    temp_state_path = PROJECT_ROOT / "state" / "test_artifacts.yaml"
    original_state_path = PROJECT_ROOT / "state" / "artifacts.yaml"

    # Backup original if exists
    if original_state_path.exists():
        shutil.copy(original_state_path, original_state_path.with_suffix(".bak"))

    try:
        # Initialize empty state
        temp_state_path.parent.mkdir(parents=True, exist_ok=True)
        save_artifacts_state({"artifacts": {}})
        # Temporarily swap paths (hack for test isolation)
        import code.data_loader as dl
        dl.STATE_FILE_PATH = temp_state_path

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"mock adapter data")
            tmp_path = Path(tmp.name)

        try:
            hash_val = register_downloaded_artifact(
                name="test_adapter",
                file_path=tmp_path,
                artifact_type="lora_adapter",
                metadata={"test": True}
            )

            state = load_artifacts_state()
            assert "test_adapter" in state["artifacts"]
            assert state["artifacts"]["test_adapter"]["hash"] == hash_val
            assert state["artifacts"]["test_adapter"]["type"] == "lora_adapter"
        finally:
            os.unlink(tmp_path)
            dl.STATE_FILE_PATH = original_state_path
    finally:
        # Restore original state
        if original_state_path.with_suffix(".bak").exists():
            shutil.move(original_state_path.with_suffix(".bak"), original_state_path)
        if temp_state_path.exists():
            os.unlink(temp_state_path)