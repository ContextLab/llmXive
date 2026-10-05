import json
import hashlib
from pathlib import Path
from argparse import Namespace

import pytest

# Import the functions we need to test
from ingestion.register_dataset import (
    register_dataset,
    compute_file_checksum,
    _verified_datasets_path,
    update_plan_with_registry_reference,
)
from utils.config import get_project_root

@pytest.fixture
def temporary_dataset(tmp_path: Path):
    """
    Create a temporary file that will act as a downloaded dataset.
    The file contains deterministic content so that its checksum is predictable.
    """
    content = b"SMILES,solvent,diffusion\\nCCO,water,1.2e-9\\n"
    file_path = tmp_path / "temp_dataset.csv"
    file_path.write_bytes(content)
    return file_path

@pytest.fixture
def clean_environment(tmp_path: Path):
    """
    Ensure a clean state: backup any existing verified_datasets.json and plan.md,
    then restore them after the test.
    """
    project_root = get_project_root()
    verified_path = project_root / "data" / "verified_datasets.json"
    plan_path = project_root / "plan.md"

    # Backup existing files if they exist
    backup_verified = None
    backup_plan = None
    if verified_path.is_file():
        backup_verified = verified_path.read_text(encoding="utf-8")
        verified_path.unlink()
    if plan_path.is_file():
        backup_plan = plan_path.read_text(encoding="utf-8")

    yield  # Run the test

    # Restore backups
    if backup_verified is not None:
        verified_path.parent.mkdir(parents=True, exist_ok=True)
        verified_path.write_text(backup_verified, encoding="utf-8")
    else:
        if verified_path.is_file():
            verified_path.unlink()
    if backup_plan is not None:
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(backup_plan, encoding="utf-8")
    else:
        if plan_path.is_file():
            plan_path.unlink()

def test_register_dataset_creates_registry_and_updates_plan(
    temporary_dataset: Path, clean_environment
):
    """
    Verify that ``register_dataset``:
    1. Writes a JSON record with the required fields to
       ``data/verified_datasets.json``.
    2. Updates ``plan.md`` with a reference line to the registry file.
    """
    project_root = get_project_root()
    verified_path = project_root / "data" / "verified_datasets.json"
    plan_path = project_root / "plan.md"

    test_url = "https://example.com/dataset.csv"
    source_type = "TestSource"

    # Ensure a clean start
    if verified_path.is_file():
        verified_path.unlink()
    if plan_path.is_file():
        # Remove any existing reference line to avoid false positives
        lines = plan_path.read_text(encoding="utf-8").splitlines()
        filtered = [l for l in lines if "Verified Datasets Registry:" not in l]
        plan_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    # Call the registration function directly
    register_dataset(
        url=test_url,
        file_path=temporary_dataset,
        source_type=source_type,
    )

    # 1. Verify the JSON registry file exists and contains the correct record
    assert verified_path.is_file(), "verified_datasets.json was not created"

    with verified_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The registry should contain exactly one entry (since we started clean)
    assert isinstance(data, list) and len(data) == 1, "Registry should contain a single entry"

    record = data[0]
    expected_checksum = compute_file_checksum(temporary_dataset)

    assert record["url"] == test_url
    assert record["source_type"] == source_type
    assert record["checksum_sha256"] == expected_checksum
    # download_date_iso should be a valid ISO‑8601 string; we check its type only
    assert isinstance(record["download_date_iso"], str)

    # 2. Verify that plan.md now contains the reference line
    reference_line = "Verified Datasets Registry: data/verified_datasets.json"
    plan_contents = plan_path.read_text(encoding="utf-8")
    assert reference_line in plan_contents, "plan.md was not updated with the registry reference"

def test_update_plan_with_registry_reference_idempotent():
    """
    Ensure that calling ``update_plan_with_registry_reference`` multiple times
    does not duplicate the reference line.
    """
    project_root = get_project_root()
    plan_path = project_root / "plan.md"

    # Start with a fresh plan file containing minimal content
    original_content = "Project Plan\n---\n"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(original_content, encoding="utf-8")

    # First call – should add the line
    update_plan_with_registry_reference(plan_path)
    first_pass = plan_path.read_text(encoding="utf-8")
    assert "Verified Datasets Registry: data/verified_datasets.json" in first_pass

    # Second call – should not add a duplicate line
    update_plan_with_registry_reference(plan_path)
    second_pass = plan_path.read_text(encoding="utf-8")
    # Count occurrences of the reference line
    occurrences = second_pass.count("Verified Datasets Registry: data/verified_datasets.json")
    assert occurrences == 1, "Reference line was duplicated in plan.md"

def test_compute_file_checksum_matches_manual_hash():
    """
    Validate that ``compute_file_checksum`` returns the correct SHA256 hash.
    """
    content = b"test content for checksum"
    test_file = Path(tmp_path) / "checksum_test.txt"
    test_file.write_bytes(content)

    # Compute expected checksum using hashlib directly
    expected = hashlib.sha256(content).hexdigest()
    assert compute_file_checksum(test_file) == expected