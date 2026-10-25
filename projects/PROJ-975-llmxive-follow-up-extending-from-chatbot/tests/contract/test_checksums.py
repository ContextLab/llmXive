"""
Contract test for T003: Verify that the checksums recorded in
`data/raw/checksums.json` match the current SHA‑256 digests of the
source files `tasks.json` and `skills.json`.
"""
import json
import pytest
from llmxive_toolkit import paths

# Import the script under test. It lives in the `code/` directory and is
# importable by its filename (without the .py extension).
from write_checksums import get_sha256, main

@pytest.fixture(scope="module")
def recomputed_checksums():
    """
    Run the checksum writer to ensure the file reflects the latest hashes.
    Returns the loaded JSON mapping.
    """
    # Execute the script's main function which overwrites the checksum file.
    main()
    checksums_path = paths.data("raw", "checksums.json")
    with open(checksums_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_tasks_checksum_matches(recomputed_checksums):
    tasks_path = paths.data("raw", "tasks.json")
    expected = get_sha256(tasks_path)
    assert recomputed_checksums.get("tasks_json_sha256") == expected, (
        "Stored tasks checksum does not match the current file hash."
    )

def test_skills_checksum_matches(recomputed_checksums):
    skills_path = paths.data("raw", "skills.json")
    expected = get_sha256(skills_path)
    assert recomputed_checksums.get("skills_json_sha256") == expected, (
        "Stored skills checksum does not match the current file hash."
    )