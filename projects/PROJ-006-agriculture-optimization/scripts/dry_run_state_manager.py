"""
Dry-run script to verify state manager functionality.

This script creates a temporary dummy file, computes its hash,
and verifies the update mechanism works correctly.
"""
import os
import tempfile
from pathlib import Path
import sys
from src.utils import state_manager
import hashlib

def main():
    """Run a dry-run test of the state manager."""
    print("=== State Manager Dry-Run Verification ===")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dummy_file = temp_path / "dummy_test_file.txt"
        
        # Write a dummy file
        dummy_content = "This is a test file for dry-run verification."
        with open(dummy_file, "w") as f:
            f.write(dummy_content)
        
        print(f"Created dummy file: {dummy_file}")
        
        # Compute hash of the dummy file
        file_hash = state_manager.compute_file_hash(dummy_file)
        print(f"Computed hash: {file_hash}")
        
        # Verify hash computation is deterministic
        file_hash_2 = state_manager.compute_file_hash(dummy_file)
        if file_hash == file_hash_2:
            print("✓ Hash computation is deterministic")
        else:
            print("✗ Hash computation is NOT deterministic")
            return False
        
        # Verify hash matches expected value
        expected_hash = hashlib.sha256(dummy_content.encode()).hexdigest()
        if file_hash == expected_hash:
            print("✓ Hash matches expected value")
        else:
            print(f"✗ Hash mismatch: expected {expected_hash}, got {file_hash}")
            return False
        
        # Test scanning a directory with the dummy file
        # We'll temporarily modify the data directory for this test
        original_data_dirs = state_manager.DATA_DIRS
        
        # Create a fake data directory structure
        fake_data_dir = temp_path / "fake_data"
        fake_data_dir.mkdir()
        (fake_data_dir / "raw").mkdir()
        (fake_data_dir / "processed").mkdir()
        
        # Copy dummy file to fake data directory
        (fake_data_dir / "raw" / "test_data.csv").write_text("col1,col2\n1,2\n")
        (fake_data_dir / "processed" / "result.json").write_text('{"status": "ok"}')
        
        # Temporarily override DATA_DIRS
        state_manager.DATA_DIRS = [fake_data_dir / "raw", fake_data_dir / "processed"]
        
        try:
            print("\nScanning fake data directories...")
            artifacts = state_manager.scan_directory_for_artifacts(fake_data_dir / "raw")
            artifacts.update(state_manager.scan_directory_for_artifacts(fake_data_dir / "processed"))
            
            print(f"Found {len(artifacts)} artifacts:")
            for path, hash_val in artifacts.items():
                print(f"  {path}: {hash_val[:16]}...")
            
            if len(artifacts) == 2:
                print("✓ Directory scan found expected number of files")
            else:
                print(f"✗ Expected 2 files, found {len(artifacts)}")
                return False
            
            # Test state loading and saving
            print("\nTesting state save/load...")
            test_state = {
                "project_id": "TEST-PROJECT",
                "last_updated": "test_run",
                "artifact_hashes": artifacts
            }
            
            test_state_file = temp_path / "test_state.yaml"
            # Temporarily override STATE_FILE for testing
            original_state_file = state_manager.STATE_FILE
            state_manager.STATE_FILE = test_state_file
            
            try:
                success = state_manager.save_state(test_state)
                if success:
                    print("✓ State saved successfully")
                else:
                    print("✗ State save failed")
                    return False
                
                loaded_state = state_manager.load_state()
                if loaded_state.get("project_id") == "TEST-PROJECT":
                    print("✓ State loaded successfully")
                else:
                    print("✗ State load failed or incorrect data")
                    return False
            finally:
                state_manager.STATE_FILE = original_state_file
            
            print("\n=== Dry-Run Verification: SUCCESS ===")
            return True
            
        finally:
            # Restore original data directories
            state_manager.DATA_DIRS = original_data_dirs

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
