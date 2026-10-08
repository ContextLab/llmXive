"""
Unit tests for design verification logic.

Tests the mindfulness intervention metadata filtering functionality
to ensure correct identification of mindfulness-related datasets.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.datasets.verify_design import (
    normalize_text,
    match_intervention_type,
    validate_metadata_fields,
    validate_design_logic,
    verify_dataset_design,
    verify_all_datasets,
    InterventionType,
    DesignMetadata,
    DesignVerificationError
)


class TestNormalizeText:
    """Tests for text normalization function."""
    
    def test_empty_string(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""
    
    def test_case_normalization(self):
        assert normalize_text("MINDFULNESS") == "mindfulness"
        assert normalize_text("MiNdFuLnEsS") == "mindfulness"
    
    def test_whitespace_normalization(self):
        assert normalize_text("  mindfulness  training  ") == "mindfulness training"
        assert normalize_text("mindfulness\t\ttraining") == "mindfulness training"
        assert normalize_text("mindfulness\n\ntraining") == "mindfulness training"
    
    def test_combined_normalization(self):
        assert normalize_text("  MBSR  Program  ") == "mbsr program"


class TestMatchInterventionType:
    """Tests for intervention type matching."""
    
    def test_mindfulness_direct(self):
        assert match_intervention_type("mindfulness") == InterventionType.MINDFULNESS
        assert match_intervention_type("Mindfulness") == InterventionType.MINDFULNESS
        assert match_intervention_type("MINDFULNESS") == InterventionType.MINDFULNESS
    
    def test_mbsr_variations(self):
        assert match_intervention_type("MBSR") == InterventionType.MBSR
        assert match_intervention_type("mindfulness-based stress reduction") == InterventionType.MBSR
        assert match_intervention_type("Mindfulness Based Stress Reduction") == InterventionType.MBSR
    
    def test_mbct_variations(self):
        assert match_intervention_type("MBCT") == InterventionType.MBCT
        assert match_intervention_type("mindfulness-based cognitive therapy") == InterventionType.MBCT
    
    def test_meditation_variations(self):
        assert match_intervention_type("meditation") == InterventionType.MEDITATION
        assert match_intervention_type("vipassana") == InterventionType.MEDITATION
        assert match_intervention_type("zen meditation") == InterventionType.MEDITATION
        assert match_intervention_type("loving-kindness") == InterventionType.MEDITATION
    
    def test_non_mindfulness(self):
        assert match_intervention_type("cognitive behavioral therapy") == InterventionType.OTHER
        assert match_intervention_type("exercise") == InterventionType.OTHER
        assert match_intervention_type("pharmacological") == InterventionType.OTHER
    
    def test_unknown(self):
        assert match_intervention_type("") == InterventionType.UNKNOWN
        assert match_intervention_type(None) == InterventionType.UNKNOWN
    
    def test_mindfulness_based_programs(self):
        assert match_intervention_type("mindfulness-based program") == InterventionType.MINDFULNESS
        assert match_intervention_type("mindfulness based training") == InterventionType.MINDFULNESS
    
    def test_march_program(self):
        assert match_intervention_type("MARCH") == InterventionType.MINDFULNESS
        assert match_intervention_type("mindfulness and resilience training") == InterventionType.MINDFULNESS


class TestValidateMetadataFields:
    """Tests for metadata field validation."""
    
    def test_valid_metadata(self):
        metadata = {
            "intervention_type": "mindfulness",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_intervention_type(self):
        metadata = {
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert not is_valid
        assert "Missing required field: intervention_type" in errors
    
    def test_invalid_intervention_type_type(self):
        metadata = {
            "intervention_type": 123,
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert not is_valid
        assert "intervention_type must be a string" in errors
    
    def test_negative_scan_count(self):
        metadata = {
            "intervention_type": "mindfulness",
            "pre_scan_count": -1,
            "post_scan_count": 10
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert not is_valid
        assert "pre_scan_count must be a non-negative integer" in errors
    
    def test_optional_fields(self):
        metadata = {
            "intervention_type": "mindfulness"
        }
        is_valid, errors = validate_metadata_fields(metadata)
        assert is_valid
        assert len(errors) == 0


class TestValidateDesignLogic:
    """Tests for design logic validation."""
    
    def test_valid_pre_post_design(self):
        metadata = {
            "intervention_type": "mindfulness",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_scan_counts_warning(self):
        metadata = {
            "intervention_type": "mindfulness"
        }
        is_valid, errors = validate_design_logic(metadata)
        # Should be valid but with a warning logged
        assert is_valid
        assert len(errors) == 0
    
    def test_zero_scan_count_error(self):
        metadata = {
            "intervention_type": "mindfulness",
            "pre_scan_count": 0,
            "post_scan_count": 10
        }
        is_valid, errors = validate_design_logic(metadata)
        assert not is_valid
        assert len(errors) > 0
    
    def test_non_mindfulness_skips_validation(self):
        metadata = {
            "intervention_type": "exercise",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid
        assert len(errors) == 0
    
    def test_empty_intervention_skips_validation(self):
        metadata = {
            "intervention_type": "",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, errors = validate_design_logic(metadata)
        assert is_valid
        assert len(errors) == 0


class TestVerifyDatasetDesign:
    """Tests for complete dataset design verification."""
    
    def test_valid_mindfulness_dataset(self):
        metadata = {
            "intervention_type": "MBSR",
            "pre_scan_count": 15,
            "post_scan_count": 15
        }
        is_valid, details = verify_dataset_design(metadata)
        assert is_valid
        assert details["is_mindfulness"]
        assert details["intervention_match"] == "MBSR"
    
    def test_invalid_missing_fields(self):
        metadata = {
            "pre_scan_count": 10
        }
        is_valid, details = verify_dataset_design(metadata)
        assert not is_valid
        assert not details["field_validation"]["is_valid"]
    
    def test_non_mindfulness_intervention(self):
        metadata = {
            "intervention_type": "cognitive behavioral therapy",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, details = verify_dataset_design(metadata)
        assert not is_valid
        assert not details["is_mindfulness"]
        assert len(details["warnings"]) > 0
    
    def test_meditation_intervention(self):
        metadata = {
            "intervention_type": "vipassana meditation",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, details = verify_dataset_design(metadata)
        assert is_valid
        assert details["is_mindfulness"]
        assert details["intervention_match"] == "meditation"
    
    def test_mbct_intervention(self):
        metadata = {
            "intervention_type": "mindfulness-based cognitive therapy",
            "pre_scan_count": 12,
            "post_scan_count": 12
        }
        is_valid, details = verify_dataset_design(metadata)
        assert is_valid
        assert details["is_mindfulness"]
        assert details["intervention_match"] == "MBCT"


class TestVerifyAllDatasets:
    """Tests for batch dataset verification."""
    
    def test_verify_multiple_datasets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create valid mindfulness dataset
            dataset1 = {
                "intervention_type": "MBSR",
                "pre_scan_count": 10,
                "post_scan_count": 10
            }
            with open(tmpdir_path / "dataset1.json", 'w') as f:
                json.dump(dataset1, f)
            
            # Create non-mindfulness dataset
            dataset2 = {
                "intervention_type": "exercise",
                "pre_scan_count": 10,
                "post_scan_count": 10
            }
            with open(tmpdir_path / "dataset2.json", 'w') as f:
                json.dump(dataset2, f)
            
            # Create meditation dataset
            dataset3 = {
                "intervention_type": "vipassana",
                "pre_scan_count": 8,
                "post_scan_count": 8
            }
            with open(tmpdir_path / "dataset3.json", 'w') as f:
                json.dump(dataset3, f)
            
            results = verify_all_datasets(tmpdir_path)
            
            assert len(results) == 3
            assert results["dataset1"]["is_valid"]
            assert not results["dataset2"]["is_valid"]
            assert results["dataset3"]["is_valid"]
    
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            results = verify_all_datasets(tmpdir_path)
            assert len(results) == 0
    
    def test_nonexistent_directory(self):
        with pytest.raises(DesignVerificationError):
            verify_all_datasets(Path("/nonexistent/path"))
    
    def test_invalid_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create invalid JSON file
            with open(tmpdir_path / "invalid.json", 'w') as f:
                f.write("{ invalid json }")
            
            results = verify_all_datasets(tmpdir_path)
            
            assert len(results) == 1
            assert "invalid" in list(results.keys())[0]
            assert not results[list(results.keys())[0]]["is_valid"]


class TestFilteringNonMindfulness:
    """Tests specifically for filtering non-mindfulness datasets."""
    
    def test_filter_exercise(self):
        metadata = {
            "intervention_type": "aerobic exercise",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert not is_valid
    
    def test_filter_pharmacological(self):
        metadata = {
            "intervention_type": "SSRI medication",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert not is_valid
    
    def test_filter_cbt(self):
        metadata = {
            "intervention_type": "cognitive behavioral therapy",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert not is_valid
    
    def test_filter_sleep_intervention(self):
        metadata = {
            "intervention_type": "sleep hygiene program",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert not is_valid
    
    def test_accept_mbsr(self):
        metadata = {
            "intervention_type": "mindfulness-based stress reduction",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert is_valid
    
    def test_accept_mbct(self):
        metadata = {
            "intervention_type": "mindfulness-based cognitive therapy",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert is_valid
    
    def test_accept_meditation(self):
        metadata = {
            "intervention_type": "mindfulness meditation",
            "pre_scan_count": 10,
            "post_scan_count": 10
        }
        is_valid, _ = verify_dataset_design(metadata)
        assert is_valid