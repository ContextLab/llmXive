import os
import tempfile
from pathlib import Path
import sys
from src.utils import state_manager
import hashlib

def main():
    """
    Dry-run hash calculation on a dummy file to confirm the update mechanism works.
    This script creates a temporary dummy file, computes its hash, updates the state,
    and verifies the update.
    """
    print("Starting dry-run hash calculation for T002...")
    
    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dummy_file = tmpdir_path / "dummy_data.csv"
        
        # Write some dummy content
        content = "household_id,CSA_Index,Stability_Score\n1,0.85,0.92\n2,0.78,0.88"
        dummy_file.write_text(content)
        
        print(f"Created dummy file: {dummy_file}")
        print(f"Content: {content}")
        
        # Compute hash manually to verify
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        computed_hash = state_manager.compute_file_hash(dummy_file)
        
        assert expected_hash == computed_hash, "Hash computation mismatch!"
        print(f"✓ Hash computed correctly: {computed_hash}")
        
        # Simulate state update
        state = {}
        project_id = "PROJ-006-agriculture-optimization"
        
        # Create a mock state path in the temp directory
        state_dir = tmpdir_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        state_path = state_dir / f"{project_id}.yaml"
        
        # Update artifacts
        updated_state = state_manager.update_artifact_hashes(state, project_id, [tmpdir_path])
        
        # Save state
        state_manager.save_state(updated_state, state_path)
        
        print(f"✓ State saved to: {state_path}")
        
        # Load and verify
        loaded_state = state_manager.load_state(state_path)
        print(f"✓ State loaded: {loaded_state}")
        
        # Verify integrity
        is_valid = state_manager.verify_artifacts(loaded_state, project_id)
        if is_valid:
            print("✓ Verification passed: Artifacts match.")
        else:
            print("✗ Verification failed.")
            return 1
        
        print("Dry-run completed successfully. T002 implementation verified.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
