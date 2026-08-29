import json
import hashlib
import sys
from pathlib import Path

# Ensure the project root is in the path if running as a script
# The project structure expects imports from src.lib.state_tracker
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lib.state_tracker import log_experiment_state, hash_parameters, generate_run_id

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of the file at file_path.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def main():
    """
    Generates a SHA-256 checksum for data/gold_standard/human_annotations.json.
    Writes the checksum to artifacts/checksums.json and updates the manifest.
    """
    project_root = Path(__file__).parent.parent
    gold_standard_path = project_root / "data" / "gold_standard" / "human_annotations.json"
    artifacts_dir = project_root / "artifacts"
    checksums_file = artifacts_dir / "checksums.json"
    manifest_file = artifacts_dir / "manifest.json"

    if not gold_standard_path.exists():
        raise FileNotFoundError(
            f"Gold standard file not found: {gold_standard_path}. "
            "Please ensure T009c has been completed successfully."
        )

    # Compute checksum
    checksum = compute_sha256(gold_standard_path)
    print(f"Computed SHA-256 for {gold_standard_path.name}: {checksum}")

    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Load existing checksums or initialize
    if checksums_file.exists():
        with open(checksums_file, "r") as f:
            checksums_data = json.load(f)
    else:
        checksums_data = {}

    # Update checksums for the specific file
    checksums_data["human_annotations.json"] = {
        "checksum": checksum,
        "algorithm": "sha256",
        "source_file": str(gold_standard_path),
        "generated_at": log_experiment_state.__module__  # Placeholder for timestamp logic if needed, or use datetime
    }

    # Write updated checksums
    with open(checksums_file, "w") as f:
        json.dump(checksums_data, f, indent=2)
    print(f"Checksums written to {checksums_file}")

    # Update manifest
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            manifest_data = json.load(f)
    else:
        manifest_data = {
            "version": "1.0",
            "files": []
        }

    # Add entry to manifest if not present
    manifest_entry = {
        "file": "human_annotations.json",
        "checksum": checksum,
        "type": "gold_standard",
        "status": "verified"
    }

    # Check if entry already exists and update, otherwise append
    found = False
    for entry in manifest_data.get("files", []):
        if entry.get("file") == "human_annotations.json":
            entry.update(manifest_entry)
            found = True
            break
    
    if not found:
        if "files" not in manifest_data:
            manifest_data["files"] = []
        manifest_data["files"].append(manifest_entry)

    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Manifest updated at {manifest_file}")

    # Log experiment state for reproducibility (Constitution Principle V)
    # We log the state of the checksum generation task
    run_id = generate_run_id()
    params = {
        "task_id": "T009a",
        "input_file": str(gold_standard_path),
        "output_checksum_file": str(checksums_file),
        "checksum": checksum
    }
    param_hash = hash_parameters(params)
    
    # Log the state
    log_experiment_state(
        run_id=run_id,
        task_id="T009a",
        status="completed",
        parameters=params,
        parameter_hash=param_hash,
        output_files=[str(checksums_file), str(manifest_file)]
    )
    print(f"Experiment state logged with run_id: {run_id}")

if __name__ == "__main__":
    main()