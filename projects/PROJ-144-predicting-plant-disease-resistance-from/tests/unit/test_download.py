import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import the module under test
from code.data.download_study import (
    get_study_download_url,
    verify_temporal_separation,
    load_phenotype_metadata,
    TemporalVerificationError
)

class TestGetStudyDownloadUrl:
    def test_url_construction(self):
        study_id = "ST001234"
        expected = f"https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID={study_id}&TYPE=STUDY"
        assert get_study_download_url(study_id) == expected

class TestVerifyTemporalSeparation:
    def test_passes_with_pre_challenge(self):
        metadata = [
            {"Sample_ID": "S1", "Time_Point": "pre-challenge", "Value": 10.5},
            {"Sample_ID": "S2", "Time_Point": "post-challenge", "Value": 12.0}
        ]
        # Should not raise
        assert verify_temporal_separation(metadata, "ST000001") is True

    def test_passes_with_baseline(self):
        metadata = [
            {"Sample_ID": "S1", "Baseline_Status": "True", "Value": 10.5}
        ]
        assert verify_temporal_separation(metadata, "ST000001") is True

    def test_passes_with_timestamp(self):
        metadata = [
            {"Sample_ID": "S1", "Time_Hours": 0, "Value": 10.5},
            {"Sample_ID": "S2", "Time_Hours": 24, "Value": 12.0}
        ]
        assert verify_temporal_separation(metadata, "ST000001") is True

    def test_fails_without_temporal_fields(self):
        metadata = [
            {"Sample_ID": "S1", "Treatment": "A", "Value": 10.5},
            {"Sample_ID": "S2", "Treatment": "B", "Value": 12.0}
        ]
        with pytest.raises(TemporalVerificationError) as excinfo:
            verify_temporal_separation(metadata, "ST000001")
        assert "lacks temporal metadata" in str(excinfo.value)

class TestLoadPhenotypeMetadata:
    def test_loads_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Sample_ID,Time_Point,Value\nS1,pre-challenge,10.5\nS2,post-challenge,12.0")
            temp_path = f.name

        try:
            data = load_phenotype_metadata(temp_path)
            assert len(data) == 2
            assert data[0]['Sample_ID'] == 'S1'
            assert data[0]['Time_Point'] == 'pre-challenge'
        finally:
            os.unlink(temp_path)

    def test_handles_missing_file(self):
        with pytest.raises(RuntimeError):
            load_phenotype_metadata("non_existent_file.csv")
