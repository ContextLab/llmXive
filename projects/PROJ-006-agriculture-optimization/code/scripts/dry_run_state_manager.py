import os
import tempfile
from pathlib import Path
import sys
from src.utils import state_manager
import hashlib

def main():
    """
    Dry-run hash calculation on a dummy file to confirm the update mechanism works.
    """
    # Create a temporary directory structure mimicking data/raw and data/processed
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        raw_dir = tmp_path / "data" / "raw"
        proc_dir = tmp_path / "data" / "processed"
        state_file = tmp_path / "state.yaml"

        raw_dir.mkdir(parents=True)
        proc_dir.mkdir(parents=True)

        # Create a dummy file
        dummy_file = raw_dir / "dummy.txt"
        dummy_content = "dry_run_test_content"
        dummy_file.write_text(dummy_content)

        # Monkeypatch paths for the test
        original_raw = state_manager.DATA_RAW_PATH
        original_proc = state_manager.DATA_PROCESSED_PATH
        original_state = state_manager.PROJECT_STATE_PATH

        state_manager.DATA_RAW_PATH = raw_dir
        state_manager.DATA_PROCESSED_PATH = proc_dir
        state_manager.PROJECT_STATE_PATH = state_file

        try:
            # Run update
            project_id = "PROJ-006-agriculture-optimization"
            print(f"Running dry-run update for project: {project_id}")
            result = state_manager.update_artifact_hashes(project_id)

            print(f"Updated state: {result}")

            # Verify the state file was created and contains the hash
            if state_file.exists():
                print(f"State file created at: {state_file}")
                with open(state_file, "r") as f:
                    content = f.read()
                    print(f"State file contents:\n{content}")

                # Verify the hash matches
                expected_hash = hashlib.sha256(dummy_content.encode()).hexdigest()
                if result["data_raw"].get("dummy.txt") == expected_hash:
                    print("SUCCESS: Hash calculation and state update verified.")
                else:
                    print("FAILURE: Hash mismatch detected.")
                    sys.exit(1)
            else:
                print("FAILURE: State file was not created.")
                sys.exit(1)

        finally:
            # Restore original paths
            state_manager.DATA_RAW_PATH = original_raw
            state_manager.DATA_PROCESSED_PATH = original_proc
            state_manager.PROJECT_STATE_PATH = original_state

if __name__ == "__main__":
    main()