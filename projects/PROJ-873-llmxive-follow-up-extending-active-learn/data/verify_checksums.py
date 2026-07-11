"""
Script to verify data integrity by recalculating checksums and comparing
against the recorded state file.
"""
import yaml
from pathlib import Path
import sys

from data_integrity import calculate_sha256


def verify_data_integrity():
    """
    Loads the state file and verifies that the checksums of current
    data files match the recorded ones.
    """
    project_id = "PROJ-873-llmxive-follow-up-extending-active-learn"
    state_file = Path("state") / "projects" / f"{project_id}.yaml"

    if not state_file.exists():
        print(f"Error: State file not found at {state_file}")
        print("Run code/data_integrity.py first to generate checksums.")
        return False

    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)

    if "artifact_hashes" not in state:
        print("Error: No artifact_hashes found in state file.")
        return False

    hashes = state["artifact_hashes"]
    all_match = True
    verified_count = 0
    error_count = 0

    for file_path, info in hashes.items():
        if not isinstance(info, dict):
            continue
        
        recorded_hash = info.get("sha256")
        if not recorded_hash:
            print(f"Skipped (no hash): {file_path}")
            continue

        if not Path(file_path).exists():
            print(f"MISSING: {file_path}")
            all_match = False
            error_count += 1
            continue

        try:
            current_hash = calculate_sha256(file_path)
            if current_hash == recorded_hash:
                print(f"OK: {file_path}")
                verified_count += 1
            else:
                print(f"FAIL: {file_path}")
                print(f"  Recorded: {recorded_hash}")
                print(f"  Current:  {current_hash}")
                all_match = False
                error_count += 1
        except Exception as e:
            print(f"ERROR reading {file_path}: {e}")
            error_count += 1

    print(f"\nSummary: {verified_count} verified, {error_count} errors.")
    return all_match


if __name__ == "__main__":
    success = verify_data_integrity()
    sys.exit(0 if success else 1)
