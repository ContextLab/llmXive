"""
Unit tests for inclusion criteria filtering logic in code/data/cleaner.py.

These tests verify that the filter_included_studies function correctly applies
the inclusion/exclusion criteria defined in the research protocol:
- Age range: 6-12 years
- Diagnosis: Must include ASD/autism
- Outcomes: Must use validated social skill measures (SRS-2, ABC, SSIS, PEP-3)
"""

import pytest
from typing import List, Dict, Any
from code.data.cleaner import filter_included_studies
from code.utils.logging import get_logger

logger = get_logger(__name__)

# Valid outcome measures whitelist
VALID_OUTCOMES = {'SRS-2', 'ABC', 'SSIS', 'PEP-3', 'SRS', 'Aberrant Behavior Checklist'}

# Test fixtures
@pytest.fixture
def valid_study() -> Dict[str, Any]:
    """A study that meets all inclusion criteria."""
    return {
        'id': 'NCT00000001',
        'title': 'Mindfulness for ASD Social Skills',
        'age_range': '6-12',
        'diagnosis': 'Autism Spectrum Disorder',
        'outcomes': ['SRS-2', 'ABC'],
        'intervention_components': ['breathing', 'body scan'],
        'delivery_format': 'caregiver-mediated'
    }

@pytest.fixture
def invalid_age_study() -> Dict[str, Any]:
    """A study with age range outside 6-12."""
    return {
        'id': 'NCT00000002',
        'title': 'Mindfulness for Teens with ASD',
        'age_range': '13-17',
        'diagnosis': 'Autism Spectrum Disorder',
        'outcomes': ['SRS-2'],
        'intervention_components': ['breathing'],
        'delivery_format': 'child-led'
    }

@pytest.fixture
def invalid_diagnosis_study() -> Dict[str, Any]:
    """A study without ASD diagnosis."""
    return {
        'id': 'NCT00000003',
        'title': 'Mindfulness for ADHD',
        'age_range': '8-12',
        'diagnosis': 'Attention Deficit Hyperactivity Disorder',
        'outcomes': ['SRS-2'],
        'intervention_components': ['breathing'],
        'delivery_format': 'caregiver-mediated'
    }

@pytest.fixture
def invalid_outcome_study() -> Dict[str, Any]:
    """A study with unvalidated outcome measures."""
    return {
        'id': 'NCT00000004',
        'title': 'Mindfulness with Custom Measures',
        'age_range': '6-12',
        'diagnosis': 'Autism Spectrum Disorder',
        'outcomes': ['Custom Survey', 'Self Report'],
        'intervention_components': ['breathing'],
        'delivery_format': 'caregiver-mediated'
    }

@pytest.fixture
def mixed_valid_invalid_studies(
    valid_study,
    invalid_age_study,
    invalid_diagnosis_study,
    invalid_outcome_study
) -> List[Dict[str, Any]]:
    """A list containing both valid and invalid studies."""
    return [
        valid_study,
        invalid_age_study,
        invalid_diagnosis_study,
        invalid_outcome_study
    ]

class TestFilterIncludedStudies:
    """Tests for the filter_included_studies function."""

    def test_valid_study_is_included(self, valid_study):
        """A study meeting all criteria should be included."""
        studies = [valid_study]
        included, excluded = filter_included_studies(studies)
        
        assert len(included) == 1
        assert included[0]['id'] == valid_study['id']
        assert len(excluded) == 0

    def test_invalid_age_study_is_excluded(self, invalid_age_study):
        """A study with age outside 6-12 should be excluded."""
        studies = [invalid_age_study]
        included, excluded = filter_included_studies(studies)
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert excluded[0]['id'] == invalid_age_study['id']
        assert excluded[0]['reason'] == 'INVALID_AGE_RANGE'

    def test_invalid_diagnosis_study_is_excluded(self, invalid_diagnosis_study):
        """A study without ASD diagnosis should be excluded."""
        studies = [invalid_diagnosis_study]
        included, excluded = filter_included_studies(studies)
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert excluded[0]['id'] == invalid_diagnosis_study['id']
        assert excluded[0]['reason'] == 'INVALID_DIAGNOSIS'

    def test_invalid_outcome_study_is_excluded(self, invalid_outcome_study):
        """A study with unvalidated outcomes should be excluded."""
        studies = [invalid_outcome_study]
        included, excluded = filter_included_studies(studies)
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert excluded[0]['id'] == invalid_outcome_study['id']
        assert excluded[0]['reason'] == 'INVALID_OUTCOME'

    def test_mixed_studies_are_correctly_filtered(self, mixed_valid_invalid_studies):
        """Mixed studies should be correctly separated into included and excluded."""
        included, excluded = filter_included_studies(mixed_valid_invalid_studies)
        
        # Should have 1 included (the valid study)
        assert len(included) == 1
        assert included[0]['id'] == mixed_valid_invalid_studies[0]['id']
        
        # Should have 3 excluded (age, diagnosis, outcome)
        assert len(excluded) == 3
        excluded_ids = {e['id'] for e in excluded}
        assert excluded_ids == {
            'NCT00000002',  # invalid age
            'NCT00000003',  # invalid diagnosis
            'NCT00000004'   # invalid outcome
        }

    def test_empty_studies_list_returns_empty(self):
        """An empty list should return empty included and excluded."""
        included, excluded = filter_included_studies([])
        
        assert len(included) == 0
        assert len(excluded) == 0

    def test_partial_age_range_inclusion(self):
        """Studies with partial overlap in age range should be included."""
        # Age range 8-10 overlaps with 6-12
        study_with_partial_age = {
            'id': 'NCT00000005',
            'title': 'Mindfulness for Younger ASD',
            'age_range': '8-10',
            'diagnosis': 'Autism Spectrum Disorder',
            'outcomes': ['SRS-2'],
            'intervention_components': ['breathing'],
            'delivery_format': 'caregiver-mediated'
        }
        
        included, excluded = filter_included_studies([study_with_partial_age])
        
        assert len(included) == 1
        assert included[0]['id'] == study_with_partial_age['id']

    def test_case_insensitive_diagnosis_check(self):
        """Diagnosis check should be case-insensitive."""
        study_lowercase = {
            'id': 'NCT00000006',
            'title': 'Mindfulness with lowercase diagnosis',
            'age_range': '6-12',
            'diagnosis': 'autism spectrum disorder',
            'outcomes': ['SRS-2'],
            'intervention_components': ['breathing'],
            'delivery_format': 'caregiver-mediated'
        }
        
        included, excluded = filter_included_studies([study_lowercase])
        
        assert len(included) == 1
        assert included[0]['id'] == study_lowercase['id']

    def test_case_insensitive_outcome_check(self):
        """Outcome check should be case-insensitive."""
        study_lowercase_outcome = {
            'id': 'NCT00000007',
            'title': 'Mindfulness with lowercase outcome',
            'age_range': '6-12',
            'diagnosis': 'Autism Spectrum Disorder',
            'outcomes': ['srs-2', 'abc'],
            'intervention_components': ['breathing'],
            'delivery_format': 'caregiver-mediated'
        }
        
        included, excluded = filter_included_studies([study_lowercase_outcome])
        
        assert len(included) == 1
        assert included[0]['id'] == study_lowercase_outcome['id']

    def test_multiple_outcomes_with_at_least_one_valid(self):
        """Study with multiple outcomes where at least one is valid should be included."""
        study_mixed_outcomes = {
            'id': 'NCT00000008',
            'title': 'Mindfulness with mixed outcomes',
            'age_range': '6-12',
            'diagnosis': 'Autism Spectrum Disorder',
            'outcomes': ['Custom Survey', 'SRS-2', 'Self Report'],
            'intervention_components': ['breathing'],
            'delivery_format': 'caregiver-mediated'
        }
        
        included, excluded = filter_included_studies([study_mixed_outcomes])
        
        assert len(included) == 1
        assert included[0]['id'] == study_mixed_outcomes['id']

    def test_multiple_outcomes_all_invalid(self):
        """Study with multiple outcomes where all are invalid should be excluded."""
        study_all_invalid_outcomes = {
            'id': 'NCT00000009',
            'title': 'Mindfulness with all invalid outcomes',
            'age_range': '6-12',
            'diagnosis': 'Autism Spectrum Disorder',
            'outcomes': ['Custom Survey', 'Self Report', 'Parent Opinion'],
            'intervention_components': ['breathing'],
            'delivery_format': 'caregiver-mediated'
        }
        
        included, excluded = filter_included_studies([study_all_invalid_outcomes])
        
        assert len(included) == 0
        assert len(excluded) == 1
        assert excluded[0]['id'] == study_all_invalid_outcomes['id']
        assert excluded[0]['reason'] == 'INVALID_OUTCOME'