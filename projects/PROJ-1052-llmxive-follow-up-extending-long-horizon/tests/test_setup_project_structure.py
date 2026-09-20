import os
import json
import subprocess
import sys
from pathlib import Path
import hashlib

def test_structure_created():
    """
    Verifies that the required directories exist and the manifest is generated.
    """
    # Run the script to ensure it executes (idempotent)
    script_path = Path("code/setup_project_structure.py")
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        # It might fail if already run, but the directory creation is idempotent.
        # We care about the result of the check, not the run itself if it's just a re-run.
        # But let's assume it runs fine.
        if result.returncode != 0:
            print(f"Script execution failed: {result.stderr}")
            # Allow failure if it's just "already exists" but we need to check files.
            # Actually, the script should not fail on existing dirs.
            assert False, f"Script failed: {result.stderr}"

    # Check directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "code/tests",
        "results",
        "artifacts",
        "specs/001-reward-fidelity-error-recovery/contracts"
    ]

    base = Path.cwd()
    for d in required_dirs:
        dir_path = base / d
        assert dir_path.is_dir(), f"Directory {d} does not exist"

    # Check manifest
    manifest_path = base / "data" / "structure_manifest.json"
    assert manifest_path.exists(), "Manifest file does not exist"

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Verify keys
    assert "directories" in manifest, "Manifest missing 'directories' key"
    assert "timestamp" in manifest, "Manifest missing 'timestamp' key"
    assert "checksum" in manifest, "Manifest missing 'checksum' key"

    # Verify directories list matches
    assert set(manifest["directories"]) == set(required_dirs), "Manifest directories list mismatch"

    # Verify checksum logic (simplified check)
    # Recalculate checksum of current state (excluding manifest itself)
    all_files = []
    for root, _, files in os.walk(base):
        for file in files:
            file_path = Path(root) / file
            if file == "structure_manifest.json":
                continue
            all_files.append(file_path)
    
    all_files.sort(key=lambda p: str(p.relative_to(base)))
    file_hashes = []
    for file_path in all_files:
        with open(file_path, "rb") as f:
            content = f.read()
            file_hashes.append(hashlib.sha256(content).hexdigest())
    
    combined = "".join(file_hashes)
    calculated_checksum = hashlib.sha256(combined.encode('utf-8')).hexdigest()

    assert manifest["checksum"] == calculated_checksum, "Checksum mismatch"

    print("All structure checks passed.")

def test_manifest_validation_via_jq_simulation():
    """
    Simulates the jq check: has("directories") and has("timestamp") and has("checksum")
    """
    manifest_path = Path("data/structure_manifest.json")
    if not manifest_path.exists():
        # Run creation first if not present
        subprocess.run([sys.executable, "code/setup_project_structure.py"], check=True)
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    has_dirs = "directories" in manifest
    has_ts = "timestamp" in manifest
    has_cs = "checksum" in manifest
    
    assert has_dirs and has_ts and has_cs, "Manifest validation failed (jq simulation)"
    print("jq simulation validation passed.")

if __name__ == "__main__":
    test_structure_created()
    test_manifest_validation_via_jq_simulation()