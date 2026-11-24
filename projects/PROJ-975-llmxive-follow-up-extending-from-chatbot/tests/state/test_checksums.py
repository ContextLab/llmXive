import json
import hashlib
import pytest
from llmxive_toolkit import paths

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def test_checksums_match_files():
    """
    Confirms that the stored digests in data/raw/checksums.json 
    exactly match the current files' SHA-256 hashes.
    """
    checksums_path = paths.data("raw", "checksums.json")
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")

    # 1. Check if checksums file exists
    assert checksums_path.exists(), "checksums.json must exist"

    # 2. Load stored checksums
    with open(checksums_path, "r", encoding="utf-8") as f:
        stored = json.load(f)

    # 3. Verify keys exist as required by T003
    assert "tasks_json_sha256" in stored, "Missing tasks_json_sha256 in checksums.json"
    assert "skills_json_sha256" in stored, "Missing skills_json_sha256 in checksums.json"

    # 4. Compare with actual current hashes
    actual_tasks_hash = get_sha256(tasks_path)
    actual_skills_hash = get_sha256(skills_path)

    assert stored["tasks_json_sha256"] == actual_tasks_hash, \
        f"Tasks hash mismatch: stored={stored['tasks_json_sha256']}, actual={actual_tasks_hash}"
    assert stored["skills_json_sha256"] == actual_skills_hash, \
        f"Skills hash mismatch: stored={stored['skills_json_sha256']}, actual={actual_skills_hash}"