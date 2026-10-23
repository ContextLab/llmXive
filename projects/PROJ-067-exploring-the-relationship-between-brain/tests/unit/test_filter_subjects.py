import json
import sys
from pathlib import Path

import pytest

# Import the main function and FatalError from the script
from code.data.filter_subjects import main, FatalError

@pytest.fixture
def temp_metadata(tmp_path):
    """Create a temporary validated metadata file with 55 subjects."""
    subjects = []
    for i in range(55):
        subjects.append({
            "subject_id": f"sub-{i:03d}",
            "dream_recall_frequency": i % 5 + 1  # valid numeric value
        })
    # Add some subjects without the field or with invalid values
    subjects.append({"subject_id": "sub-999", "dream_recall_frequency": None})
    subjects.append({"subject_id": "sub-998", "dream_recall_frequency": "N/A"})
    metadata_path = tmp_path / "validated_metadata.json"
    metadata_path.write_text(json.dumps(subjects), encoding="utf-8")
    return metadata_path

@pytest.fixture
def config_override(monkeypatch, temp_metadata):
    """Override config paths for the test."""
    from code.utils import config as cfg
    monkeypatch.setattr(cfg, "get_config_summary", lambda: {
        "metadata_path": str(temp_metadata),
        "valid_subjects_path": str(temp_metadata.parent / "valid_subjects.json"),
        "target_subject_count": 50
    })

def test_successful_filtering(tmp_path, config_override):
    """Ensure that exactly 50 subjects are written when enough valid entries exist."""
    # Run the script
    exit_code = main()
    assert exit_code == 0

    # Verify the output file exists and contains 50 entries
    output_path = Path("data/raw/valid_subjects.json")
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 50
    # Ensure they are sorted by subject_id
    ids = [s["subject_id"] for s in data]
    assert ids == sorted(ids)

def test_insufficient_subjects(tmp_path, monkeypatch):
    """When fewer than 50 valid subjects are present, FatalError should be raised."""
    # Create a metadata file with only 30 valid subjects
    subjects = [
        {"subject_id": f"sub-{i:03d}", "dream_recall_frequency": 1}
        for i in range(30)
    ]
    metadata_path = tmp_path / "validated_metadata.json"
    metadata_path.write_text(json.dumps(subjects), encoding="utf-8")

    # Override config to point to this temporary file
    from code.utils import config as cfg
    monkeypatch.setattr(cfg, "get_config_summary", lambda: {
        "metadata_path": str(metadata_path),
        "valid_subjects_path": str(tmp_path / "valid_subjects.json"),
        "target_subject_count": 50
    })

    with pytest.raises(FatalError, match="Insufficient subjects for N=50 target"):
        main()