"""
Verification script for T005b: Runs versioning.py on a dummy artifact
and verifies the state YAML is updated correctly.

This script creates a temporary dummy file, runs the versioning logic,
and validates the output state file.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from versioning import (
    compute_sha256,
    load_state,
    update_version_state
)

def main():
    """Run verification of versioning.py on a dummy artifact."""
    print("=" * 60)
    print("T005b Verification: Running versioning.py on dummy artifact")
    print("=" * 60)
    
    # Create a temporary directory for this verification run
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a dummy artifact
        dummy_file = tmp_path / "verification_dummy.txt"
        dummy_content = f"Dummy artifact created at {datetime.utcnow().isoformat()} for T005b verification."
        dummy_file.write_text(dummy_content)
        print(f"\n1. Created dummy artifact: {dummy_file}")
        
        # Compute expected hash
        expected_hash = compute_sha256(dummy_file)
        print(f"   Computed hash: {expected_hash[:32]}...")
        
        # Define state file location
        state_file = tmp_path / "verification_state.yaml"
        print(f"\n2. State file will be written to: {state_file}")
        
        # Run update_version_state
        print("\n3. Running update_version_state()...")
        try:
            state = update_version_state(
                targets=["verification_dummy.txt"],
                state_file=state_file,
                project_root=tmp_path
            )
            print("   ✓ update_version_state() completed successfully")
        except Exception as e:
            print(f"   ✗ ERROR: update_version_state() failed: {e}")
            return False
        
        # Verify state file exists
        if not state_file.exists():
            print(f"   ✗ ERROR: State file was not created at {state_file}")
            return False
        print(f"\n4. ✓ State file created: {state_file}")
        
        # Load and validate state
        print("\n5. Validating state file contents...")
        try:
            with open(state_file, 'r') as f:
                loaded_state = yaml.safe_load(f)
        except Exception as e:
            print(f"   ✗ ERROR: Failed to load state file: {e}")
            return False
        
        # Check required fields
        checks = [
            ("last_updated", "Timestamp field"),
            ("project", "Project identifier"),
            ("artifacts", "Artifacts dictionary"),
        ]
        
        all_passed = True
        for field, description in checks:
            if field not in loaded_state:
                print(f"   ✗ ERROR: Missing {description} ('{field}')")
                all_passed = False
            else:
                print(f"   ✓ {description} present: {field} = {str(loaded_state[field])[:50]}...")
        
        # Check project name
        if loaded_state.get("project") != "PROJ-786-multi-property-trade-offs-in-alloy-desig":
            print(f"   ✗ ERROR: Project name mismatch")
            all_passed = False
        else:
            print(f"   ✓ Project name matches: PROJ-786-multi-property-trade-offs-in-alloy-desig")
        
        # Check artifact entry
        if "verification_dummy.txt" not in loaded_state.get("artifacts", {}):
            print(f"   ✗ ERROR: Dummy artifact not found in artifacts")
            all_passed = False
        else:
            artifact_info = loaded_state["artifacts"]["verification_dummy.txt"]
            
            # Verify type
            if artifact_info.get("type") != "file":
                print(f"   ✗ ERROR: Artifact type is not 'file'")
                all_passed = False
            else:
                print(f"   ✓ Artifact type: file")
            
            # Verify hash
            if artifact_info.get("hash") != expected_hash:
                print(f"   ✗ ERROR: Hash mismatch")
                print(f"      Expected: {expected_hash}")
                print(f"      Got:      {artifact_info.get('hash')}")
                all_passed = False
            else:
                print(f"   ✓ Hash matches computed value")
            
            # Verify path
            if artifact_info.get("path") != "verification_dummy.txt":
                print(f"   ✗ ERROR: Path mismatch")
                all_passed = False
            else:
                print(f"   ✓ Path is correct")
        
        # Print summary
        print("\n" + "=" * 60)
        if all_passed:
            print("T005b VERIFICATION: PASSED")
            print("  - versioning.py executed successfully")
            print("  - Dummy artifact hashed correctly")
            print("  - State YAML updated with valid structure")
            print("=" * 60)
            return True
        else:
            print("T005b VERIFICATION: FAILED")
            print("  - One or more validation checks failed")
            print("=" * 60)
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)