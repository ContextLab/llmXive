"""
Utility to apply the spec amendments patch and verify the changes.
"""
import os
import subprocess
from pathlib import Path

def apply_patch(patch_path: str, target_path: str) -> bool:
    """
    Applies a unified diff patch to the target file.
    Returns True if successful, False otherwise.
    """
    try:
        # Check if patch file exists
        if not os.path.exists(patch_path):
            print(f"Error: Patch file not found at {patch_path}")
            return False

        # Check if target file exists
        if not os.path.exists(target_path):
            print(f"Error: Target file not found at {target_path}")
            return False

        # Apply the patch
        result = subprocess.run(
            ["patch", "-p1", "-i", patch_path],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error applying patch: {result.stderr}")
            return False

        print(f"Successfully applied patch to {target_path}")
        return True

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def verify_amendments(target_path: str) -> bool:
    """
    Verifies that the spec.md file contains the required amendments.
    """
    try:
        with open(target_path, 'r') as f:
            content = f.read()

        required_changes = [
            "Linear Mixed Models (LMM)",
            "prompt token count",
            "manual review queue",
            "diagnostic proxy only"
        ]

        missing = []
        for change in required_changes:
            if change not in content:
                missing.append(change)

        if missing:
            print(f"Verification failed. Missing amendments: {missing}")
            return False

        print("Verification successful. All required amendments are present.")
        return True

    except Exception as e:
        print(f"Error verifying amendments: {e}")
        return False

def main():
    """
    Main entry point to apply and verify spec amendments.
    """
    project_root = Path(__file__).parent.parent
    patch_file = project_root / "spec_amendments.patch"
    spec_file = project_root / "spec.md"

    print("Applying spec amendments...")
    if not apply_patch(str(patch_file), str(spec_file)):
        print("Failed to apply patch.")
        return 1

    print("Verifying amendments...")
    if not verify_amendments(str(spec_file)):
        print("Verification failed.")
        return 1

    print("Task T001 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())