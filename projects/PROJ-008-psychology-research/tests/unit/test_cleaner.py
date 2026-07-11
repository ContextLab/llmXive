"""
Unit tests for the data cleaner module.

Tests the inclusion criteria filtering logic:
1. Age range overlap (6-12)
2. ASD diagnosis presence
3. Social skill outcome presence
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.cleaner import (
    _check_age_overlap,
    _has_asd_diagnosis,
    _has_social_outcome,
    filter_included_studies
)

class TestAgeOverlap:
    """Tests for _check_age_overlap function."""
    
    def test_complete_overlap(self):
        """Study age range fully within target range."""
        assert _check_age_overlap(8, 10) is True
    
    def test_partial_overlap_low(self):
        """Study age range partially overlaps at lower end."""
        assert _check_age_overlap(4, 8) is True
    
    def test_partial_overlap_high(self):
        """Study age range partially overlaps at higher end."""
        assert _check_age_overlap(10, 15) is True
    
    def test_no_overlap_below(self):
        """Study age range completely below target."""
        assert _check_age_overlap(2, 5) is False
    
    def test_no_overlap_above(self):
        """Study age range completely above target."""
        assert _check_age_overlap(13, 18) is True  # 13 > 12, but 18 >= 6, so overlap at boundary? No: 13 <= 12 is False
        # Actually: 13 <= 12 is False, so no overlap
        assert _check_age_overlap(13, 18) is False
    
    def test_boundary_exact_low(self):
        """Study age range exactly at lower boundary."""
        assert _check_age_overlap(6, 8) is True
    
    def test_boundary_exact_high(self):
        """Study age range exactly at upper boundary."""
        assert _check_age_overlap(10, 12) is True
    
    def test_none_values(self):
        """None values should return False."""
        assert _check_age_overlap(None, 10) is False
        assert _check_age_overlap(6, None) is False
        assert _check_age_overlap(None, None) is False

class TestASDDiagnosis:
    """Tests for _has_asd_diagnosis function."""
    
    def test_asd_exact(self):
        """Exact match for ASD."""
        assert _has_asd_diagnosis(["asd"]) is True
    
    def test_autism_exact(self):
        """Exact match for autism."""
        assert _has_asd_diagnosis(["autism"]) is True
    
    def test_autism_spectrum_disorder(self):
        """Full phrase match."""
        assert _has_asd_diagnosis(["autism spectrum disorder"]) is True
    
    def test_autistic(self):
        """Adjective form."""
        assert _has_asd_diagnosis(["autistic children"]) is True
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert _has_asd_diagnosis(["ASD"]) is True
        assert _has_asd_diagnosis(["Autism"]) is True
    
    def test_multiple_diagnoses_with_asd(self):
        """Multiple diagnoses including ASD."""
        assert _has_asd_diagnosis(["adhd", "asd", "anxiety"]) is True
    
    def test_no_asd(self):
        """No ASD diagnosis present."""
        assert _has_asd_diagnosis(["adhd", "anxiety", "depression"]) is False
    
    def test_empty_list(self):
        """Empty diagnosis list."""
        assert _has_asd_diagnosis([]) is False
    
    def test_none_list(self):
        """None diagnosis list."""
        assert _has_asd_diagnosis(None) is False

class TestSocialOutcome:
    """Tests for _has_social_outcome function."""
    
    def test_social_skills(self):
        """Exact match for social skills."""
        assert _has_social_outcome(["social skills"]) is True
    
    def test_social_interaction(self):
        """Social interaction outcome."""
        assert _has_social_outcome(["social interaction"]) is True
    
    def test_peer_interaction(self):
        """Peer interaction outcome."""
        assert _has_social_outcome(["peer interaction"]) is True
    
    def test_communication(self):
        """Communication outcome."""
        assert _has_social_outcome(["communication skills"]) is True
    
    def test_relationship(self):
        """Relationship outcome."""
        assert _has_social_outcome(["peer relationships"]) is True
    
    def test_social_responsiveness(self):
        """Social responsiveness scale."""
        assert _has_social_outcome(["social responsiveness scale"]) is True
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert _has_social_outcome(["SOCIAL SKILLS"]) is True
        assert _has_social_outcome(["Social Interaction"]) is True
    
    def test_multiple_outcomes_with_social(self):
        """Multiple outcomes including social."""
        assert _has_social_outcome(["academic performance", "social skills", "behavior"]) is True
    
    def test_no_social_outcome(self):
        """No social skill outcome present."""
        assert _has_social_outcome(["academic performance", "motor skills", "sleep"]) is False
    
    def test_empty_list(self):
        """Empty outcome list."""
        assert _has_social_outcome([]) is False
    
    def test_none_list(self):
        """None outcome list."""
        assert _has_social_outcome(None) is False

class TestFilterIncludedStudies:
    """Tests for the main filter_included_studies function."""
    
    def test_all_criteria_met(self):
        """Study meets all inclusion criteria."""
        studies = [
            {
                "study_id": "test_001",
                "age_min": 8,
                "age_max": 12,
                "diagnosis": ["asd"],
                "outcomes": ["social skills"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 1
        assert result[0]["study_id"] == "test_001"
    
    def test_age_excluded(self):
        """Study excluded due to age range."""
        studies = [
            {
                "study_id": "test_002",
                "age_min": 14,
                "age_max": 18,
                "diagnosis": ["asd"],
                "outcomes": ["social skills"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 0
    
    def test_diagnosis_excluded(self):
        """Study excluded due to lack of ASD diagnosis."""
        studies = [
            {
                "study_id": "test_003",
                "age_min": 8,
                "age_max": 12,
                "diagnosis": ["adhd"],
                "outcomes": ["social skills"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 0
    
    def test_outcome_excluded(self):
        """Study excluded due to lack of social outcome."""
        studies = [
            {
                "study_id": "test_004",
                "age_min": 8,
                "age_max": 12,
                "diagnosis": ["asd"],
                "outcomes": ["academic performance"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 0
    
    def test_multiple_studies_mixed(self):
        """Multiple studies with mixed inclusion status."""
        studies = [
            {
                "study_id": "included_1",
                "age_min": 7,
                "age_max": 11,
                "diagnosis": ["autism"],
                "outcomes": ["peer interaction"]
            },
            {
                "study_id": "excluded_age",
                "age_min": 15,
                "age_max": 17,
                "diagnosis": ["asd"],
                "outcomes": ["social skills"]
            },
            {
                "study_id": "included_2",
                "age_min": 6,
                "age_max": 12,
                "diagnosis": ["autism spectrum disorder"],
                "outcomes": ["social communication"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 2
        included_ids = [s["study_id"] for s in result]
        assert "included_1" in included_ids
        assert "included_2" in included_ids
        assert "excluded_age" not in included_ids
    
    def test_empty_input(self):
        """Empty input list."""
        result = filter_included_studies([])
        assert len(result) == 0
    
    def test_missing_fields(self):
        """Studies with missing fields should be excluded."""
        studies = [
            {
                "study_id": "missing_age",
                "diagnosis": ["asd"],
                "outcomes": ["social skills"]
            },
            {
                "study_id": "missing_diagnosis",
                "age_min": 8,
                "age_max": 12,
                "outcomes": ["social skills"]
            },
            {
                "study_id": "missing_outcome",
                "age_min": 8,
                "age_max": 12,
                "diagnosis": ["asd"]
            }
        ]
        result = filter_included_studies(studies)
        assert len(result) == 0