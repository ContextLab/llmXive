"""
Unit tests for T073b: mock_recruitment.py
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.mock_recruitment import main, MIN_PARTICIPANTS

class TestMockRecruitment:
    
    def test_output_file_creation(self):
        """Assert that the script creates the output file."""
        # We run the main function which writes to data/raw/participants_raw.json
        # We need to ensure the directory exists for the test
        data_dir = project_root / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        result = main()
        
        output_path = project_root / "data" / "raw" / "participants_raw.json"
        assert output_path.exists(), "Output file participants_raw.json was not created"
        assert result == 0, "Script returned non-zero exit code"

    def test_minimum_participant_count(self):
        """Assert that at least MIN_PARTICIPANTS records are generated."""
        output_path = project_root / "data" / "raw" / "participants_raw.json"
        
        # Ensure file exists first
        if not output_path.exists():
            main()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        participants = data.get("participants", [])
        assert len(participants) >= MIN_PARTICIPANTS, \
            f"Expected at least {MIN_PARTICIPANTS} participants, found {len(participants)}"

    def test_participant_structure(self):
        """Assert that each participant record has the required fields."""
        output_path = project_root / "data" / "raw" / "participants_raw.json"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        participants = data.get("participants", [])
        required_fields = ["participant_id", "recruitment_timestamp", "demographics", "status"]
        demo_fields = ["experience_level", "years_experience", "primary_language"]
        
        for p in participants:
            for field in required_fields:
                assert field in p, f"Missing field '{field}' in participant record"
            
            for demo_field in demo_fields:
                assert demo_field in p.get("demographics", {}), \
                    f"Missing demographics field '{demo_field}'"
            
            # Verify ID is a valid UUID string
            import uuid
            try:
                uuid.UUID(p["participant_id"])
            except ValueError:
                pytest.fail(f"participant_id '{p['participant_id']}' is not a valid UUID")

    def test_metadata_structure(self):
        """Assert that the dataset metadata is present and valid."""
        output_path = project_root / "data" / "raw" / "participants_raw.json"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data, "Dataset missing 'metadata' key"
        meta = data["metadata"]
        assert "total_count" in meta, "Metadata missing 'total_count'"
        assert "task_id" in meta, "Metadata missing 'task_id'"
        assert meta["task_id"] == "T073b", "Task ID mismatch in metadata"