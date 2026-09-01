"""
Unit tests for inclusion criteria filtering logic in code/data/cleaner.py.

This module verifies that the filter_included_studies function correctly
applies the inclusion criteria defined in the research protocol:
1. Age range must be 6-12 years (inclusive)
2. Diagnosis must include ASD (Autism Spectrum Disorder)
3. Outcomes must include social skill measures
"""

import pytest
from typing import List, Dict, Any
from code.data.cleaner import filter_included_studies
from code.data.models import Study, RegistrySource, BlindingStatus


class TestInclusionCriteriaFiltering:
    """Test suite for the inclusion criteria filtering logic."""

    def _create_test_study(
        self,
        study_id: str = "test_001",
        title: str = "Test Study",
        registry: str = "ClinicalTrials.gov",
        age_range: str = "6-12",
        diagnosis: str = "ASD",
        outcomes: List[str] = None,
        intervention_components: List[str] = None,
        delivery_format: str = "Group",
        follow_up: str = "3-month",
        assessor_blinding: str = "single-blind",
        abstract_text: str = None
    ) -> Dict[str, Any]:
        """Helper to create a test study dictionary."""
        if outcomes is None:
            outcomes = ["social skills"]
        if intervention_components is None:
            intervention_components = ["mindfulness"]

        return {
            "id": study_id,
            "title": title,
            "registry": registry,
            "age_range": age_range,
            "diagnosis": diagnosis,
            "outcomes": outcomes,
            "intervention_components": intervention_components,
            "delivery_format": delivery_format,
            "follow_up": follow_up,
            "assessor_blinding": assessor_blinding,
            "abstract_text": abstract_text
        }

    def test_all_criteria_met_included(self):
        """Studies meeting all criteria should be included."""
        studies = [
            self._create_test_study(
                study_id="S001",
                age_range="6-12",
                diagnosis="ASD",
                outcomes=["social skills", "communication"]
            ),
            self._create_test_study(
                study_id="S002",
                age_range="8-10",
                diagnosis="Autism Spectrum Disorder",
                outcomes=["social interaction"]
            )
        ]

        included, excluded = filter_included_studies(studies)

        assert len(included) == 2
        assert len(excluded) == 0
        assert included[0]["id"] == "S001"
        assert included[1]["id"] == "S002"

    def test_age_out_of_range_excluded(self):
        """Studies with age range outside 6-12 should be excluded."""
        studies = [
            self._create_test_study(
                study_id="S001",
                age_range="6-12",
                diagnosis="ASD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S002",
                age_range="13-17",
                diagnosis="ASD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S003",
                age_range="4-8",
                diagnosis="ASD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S004",
                age_range="18-25",
                diagnosis="ASD",
                outcomes=["social skills"]
            )
        ]

        included, excluded = filter_included_studies(studies)

        assert len(included) == 1
        assert len(excluded) == 3
        assert included[0]["id"] == "S001"
        excluded_ids = [s["id"] for s in excluded]
        assert "S002" in excluded_ids
        assert "S003" in excluded_ids
        assert "S004" in excluded_ids

    def test_non_asd_diagnosis_excluded(self):
        """Studies without ASD diagnosis should be excluded."""
        studies = [
            self._create_test_study(
                study_id="S001",
                diagnosis="ASD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S002",
                diagnosis="ADHD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S003",
                diagnosis="Anxiety Disorder",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S004",
                diagnosis="Typical Development",
                outcomes=["social skills"]
            )
        ]

        included, excluded = filter_included_studies(studies)

        assert len(included) == 1
        assert len(excluded) == 3
        assert included[0]["id"] == "S001"
        excluded_ids = [s["id"] for s in excluded]
        assert "S002" in excluded_ids
        assert "S003" in excluded_ids
        assert "S004" in excluded_ids

    def test_no_social_skill_outcomes_excluded(self):
        """Studies without social skill outcomes should be excluded."""
        studies = [
            self._create_test_study(
                study_id="S001",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S002",
                outcomes=["academic achievement"]
            ),
            self._create_test_study(
                study_id="S003",
                outcomes=["motor skills", "cognitive function"]
            ),
            self._create_test_study(
                study_id="S004",
                outcomes=[]
            )
        ]

        included, excluded = filter_included_studies(studies)

        assert len(included) == 1
        assert len(excluded) == 3
        assert included[0]["id"] == "S001"
        excluded_ids = [s["id"] for s in excluded]
        assert "S002" in excluded_ids
        assert "S003" in excluded_ids
        assert "S004" in excluded_ids

    def test_asd_variations_included(self):
        """Various ASD terminology should be included."""
        studies = [
            self._create_test_study(study_id="S001", diagnosis="ASD"),
            self._create_test_study(study_id="S002", diagnosis="Autism Spectrum Disorder"),
            self._create_test_study(study_id="S003", diagnosis="Autism"),
            self._create_test_study(study_id="S004", diagnosis="Pervasive Developmental Disorder"),
        ]

        included, excluded = filter_included_studies(studies)

        # All should be included as they all relate to ASD
        assert len(included) == 4
        assert len(excluded) == 0

    def test_empty_studies_list(self):
        """Empty input should return empty output."""
        included, excluded = filter_included_studies([])

        assert len(included) == 0
        assert len(excluded) == 0

    def test_combined_criteria_failure(self):
        """Studies failing multiple criteria should be excluded."""
        studies = [
            self._create_test_study(
                study_id="S001",
                age_range="6-12",
                diagnosis="ASD",
                outcomes=["social skills"]
            ),
            self._create_test_study(
                study_id="S002",
                age_range="14-18",  # Age fail
                diagnosis="ADHD",  # Diagnosis fail
                outcomes=["academic achievement"]  # Outcome fail
            )
        ]

        included, excluded = filter_included_studies(studies)

        assert len(included) == 1
        assert len(excluded) == 1
        assert included[0]["id"] == "S001"
        assert excluded[0]["id"] == "S002"

    def test_boundary_age_values(self):
        """Test exact boundary values for age range."""
        studies = [
            self._create_test_study(study_id="S001", age_range="6-12"),
            self._create_test_study(study_id="S002", age_range="6-6"),
            self._create_test_study(study_id="S003", age_range="12-12"),
            self._create_test_study(study_id="S004", age_range="5-12"),  # 5 is out
            self._create_test_study(study_id="S005", age_range="6-13"),  # 13 is out
        ]

        included, excluded = filter_included_studies(studies)

        # S001, S002, S003 should be included (all within 6-12)
        # S004 (starts at 5) and S005 (ends at 13) should be excluded
        assert len(included) == 3
        assert len(excluded) == 2
        included_ids = [s["id"] for s in included]
        assert "S001" in included_ids
        assert "S002" in included_ids
        assert "S003" in included_ids
        excluded_ids = [s["id"] for s in excluded]
        assert "S004" in excluded_ids
        assert "S005" in excluded_ids

    def test_case_insensitive_outcome_matching(self):
        """Outcome matching should be case-insensitive."""
        studies = [
            self._create_test_study(study_id="S001", outcomes=["Social Skills"]),
            self._create_test_study(study_id="S002", outcomes=["SOCIAL SKILLS"]),
            self._create_test_study(study_id="S003", outcomes=["social interaction"]),
            self._create_test_study(study_id="S004", outcomes=["Communication"]),
        ]

        included, excluded = filter_included_studies(studies)

        # S001, S002, S003 should be included (contain social-related terms)
        # S004 should be excluded (no social skill term)
        assert len(included) == 3
        assert len(excluded) == 1
        assert included[0]["id"] == "S001"
        assert included[1]["id"] == "S002"
        assert included[2]["id"] == "S003"
        assert excluded[0]["id"] == "S004"