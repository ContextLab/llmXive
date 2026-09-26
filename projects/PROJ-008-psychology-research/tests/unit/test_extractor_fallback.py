import json
import os
import tempfile
from pathlib import Path
import pytest

from code.data.extractor import process_studies_with_fallback, log_excluded_study

class TestAbstractFallback:
    """Tests for T020: Abstract-only text extraction fallback."""

    def test_missing_metadata_with_abstract_fallback(self, tmp_path):
        """
        Verify that if age_range, diagnosis, or outcomes are missing,
        but an abstract is present, the study is processed using the abstract.
        """
        # Mock study missing 'age_range' but has 'abstract'
        study_missing_age = {
            "id": "test-study-1",
            "title": "Test Study Missing Age",
            "diagnosis": "ASD",
            "outcomes": ["social skill improvement"],
            # age_range is missing
            "abstract": "This study involves children aged 8-12 with ASD focusing on breathing exercises and peer interaction.",
            "description": ""
        }

        excluded_log_path = tmp_path / "excluded_studies.log"
        
        studies = [study_missing_age]
        processed = process_studies_with_fallback(studies, excluded_log_path)

        # Should have processed 1 study
        assert len(processed) == 1
        assert processed[0]["id"] == "test-study-1"
        
        # Verify extraction happened from abstract (e.g., breathing component detected)
        assert "breathing" in processed[0].get("intervention_components", [])
        assert processed[0].get("social_skill_domain") == "peer interaction"
        
        # Log should be empty
        assert not excluded_log_path.exists()

    def test_missing_metadata_no_abstract_excluded(self, tmp_path):
        """
        Verify that if metadata is missing AND abstract is missing,
        the study is logged as excluded with reason INSUFFICIENT_METADATA_NO_ABSTRACT.
        """
        study_missing_all = {
            "id": "test-study-2",
            "title": "Test Study No Data",
            # Missing age_range, diagnosis, outcomes
            "abstract": None,
            "description": ""
        }

        excluded_log_path = tmp_path / "excluded_studies.log"
        
        studies = [study_missing_all]
        processed = process_studies_with_fallback(studies, excluded_log_path)

        # Should have processed 0 studies
        assert len(processed) == 0
        
        # Verify exclusion log exists and contains the entry
        assert excluded_log_path.exists()
        with open(excluded_log_path, "r") as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry["study_id"] == "test-study-2"
            assert entry["reason"] == "INSUFFICIENT_METADATA_NO_ABSTRACT"

    def test_complete_metadata_standard_extraction(self, tmp_path):
        """
        Verify that if all metadata is present, standard extraction occurs
        without checking abstract fallback.
        """
        study_complete = {
            "id": "test-study-3",
            "title": "Test Study Complete",
            "age_range": {"min": 8, "max": 12},
            "diagnosis": "ASD",
            "outcomes": ["social skill improvement"],
            "abstract": "This is a valid abstract.",
            "description": "This study involves mindful eating."
        }

        excluded_log_path = tmp_path / "excluded_studies.log"
        
        studies = [study_complete]
        processed = process_studies_with_fallback(studies, excluded_log_path)

        assert len(processed) == 1
        # Should extract from description, not abstract
        assert "mindful eating" in processed[0].get("intervention_components", [])
        assert not excluded_log_path.exists()

    def test_mock_record_2_scenario(self, tmp_path):
        """
        Specific test for T015b Record 2 scenario:
        Valid study, age 10, ASD, social outcome, NO abstract.
        Wait, T015b Record 2 says: "NO abstract (to trigger T020 exclusion logic if metadata is missing)".
        But the record description says "Valid study, age 10...".
        If it has age, diagnosis, outcomes, it is NOT missing metadata.
        The task T020 logic says: "Define 'insufficient metadata' as the absence of ANY of the three mandatory inclusion fields".
        If Record 2 has all three, it should NOT be excluded.
        
        However, the task description for T020 says: "Use data/raw/mock_registry_response.json (T015b, Record 2) to trigger and verify this path."
        This implies Record 2 in the mock data is constructed to have MISSING metadata fields.
        Let's assume the mock data for Record 2 is missing 'age_range' or 'diagnosis' or 'outcomes' AND has no abstract.
        We simulate that here.
        """
        # Simulating the specific case where Record 2 is missing 'age_range' and has no abstract
        study_record_2_variant = {
            "id": "record-2-missing-age",
            "title": "Record 2 Missing Age",
            "diagnosis": "ASD",
            "outcomes": ["social skill"],
            # age_range is missing
            "abstract": None,
            "description": ""
        }

        excluded_log_path = tmp_path / "excluded_studies.log"
        
        studies = [study_record_2_variant]
        processed = process_studies_with_fallback(studies, excluded_log_path)

        assert len(processed) == 0
        assert excluded_log_path.exists()
        with open(excluded_log_path, "r") as f:
            entry = json.loads(f.readline())
            assert entry["reason"] == "INSUFFICIENT_METADATA_NO_ABSTRACT"

    def test_mock_record_2_with_abstract(self, tmp_path):
        """
        Simulating Record 2 if it had an abstract but missing metadata.
        """
        study_record_2_with_abstract = {
            "id": "record-2-with-abstract",
            "title": "Record 2 With Abstract",
            "diagnosis": "ASD",
            "outcomes": ["social skill"],
            "age_range": None, # Explicitly missing
            "abstract": "Study on 10 year olds with ASD doing breathing.",
            "description": ""
        }

        excluded_log_path = tmp_path / "excluded_studies.log"
        
        studies = [study_record_2_with_abstract]
        processed = process_studies_with_fallback(studies, excluded_log_path)

        assert len(processed) == 1
        assert "breathing" in processed[0].get("intervention_components", [])
        assert not excluded_log_path.exists()
