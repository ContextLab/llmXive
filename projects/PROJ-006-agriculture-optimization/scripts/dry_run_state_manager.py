"""
Dry-run script to verify state_manager functionality.
Creates a dummy file, computes its hash, and updates the state file.
"""
import os
import tempfile
from pathlib import Path
import sys
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import state_manager
from src.utils.io_helpers import FatalError


def main():
    print("=== State Manager Dry Run ===")
    print("Creating temporary data structure for testing...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Setup mock data directories
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Create a dummy file in data/raw
        dummy_file = raw_dir / "dummy_data.txt"
        dummy_content = "This is a dummy file for dry-run testing.\nLine 2."
        dummy_file.write_text(dummy_content)
        print(f"Created dummy file: {dummy_file}")
        
        # Compute expected hash
        expected_hash = hashlib.sha256(dummy_content.encode()).hexdigest()
        print(f"Expected hash: {expected_hash}")
        
        # Patch the state_manager module to use our temp directories
        with state_manager.patch.object(state_manager, 'STATE_DIR', state_dir):
            with state_manager.patch.object(state_manager, 'DATA_RAW_DIR', raw_dir):
                with state_manager.patch.object(state_manager, 'DATA_PROCESSED_DIR', processed_dir):
                    # Update state
                    print("\nUpdating artifact hashes...")
                    try:
                        updated_state = state_manager.update_artifact_hashes()
                        print("✓ State updated successfully")
                        
                        # Verify the hash was recorded correctly
                        recorded_hash = updated_state['artifacts']['data/raw'].get('dummy_data.txt')
                        if recorded_hash == expected_hash:
                            print(f"✓ Hash verification passed: {recorded_hash}")
                        else:
                            print(f"✗ Hash mismatch! Expected: {expected_hash}, Got: {recorded_hash}")
                            return 1
                        
                        # Verify artifacts
                        print("\nVerifying artifacts...")
                        if state_manager.verify_artifacts():
                            print("✓ All artifacts verified successfully")
                        else:
                            print("✗ Artifact verification failed")
                            return 1
                            
                    except FatalError as e:
                        print(f"✗ Fatal error during update: {e}")
                        return 1
                    except Exception as e:
                        print(f"✗ Unexpected error: {e}")
                        return 1
    
    print("\n=== Dry Run Completed Successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())