import pytest
import json
from code.extraction import extract_planned_metrics, fetch_study_pre_registration_data, ExtractionError

class TestExtractPlannedMetrics:
    def test_extract_power(self):
        text = "We aim for a power of 0.80 to detect the effect."
        res = extract_planned_metrics(text)
        assert res.get('planned_power') == 0.80

    def test_extract_power_percentage(self):
        text = "Target power: 90% for the study."
        res = extract_planned_metrics(text)
        assert res.get('planned_power') == 0.90

    def test_extract_target_n(self):
        text = "Sample size will be N = 50 participants."
        res = extract_planned_metrics(text)
        assert res.get('target_n') == 50

    def test_extract_effect_size(self):
        text = "Assuming an effect size d = 0.5."
        res = extract_planned_metrics(text)
        assert res.get('effect_size_assumption') == 0.5

    def test_missing_data_returns_empty(self):
        text = "No statistical details provided here."
        res = extract_planned_metrics(text)
        assert res == {}

    def test_empty_text(self):
        res = extract_planned_metrics("")
        assert res == {}

class TestFetchStudyPreRegistrationData:
    def test_missing_data_flag(self, mocker):
        # Mock get_study_metadata to return no pre-registrations
        mocker.patch('code.extraction.get_study_metadata', return_value={
            'pre_registrations': []
        })
        result = fetch_study_pre_registration_data("fake-id-123")
        assert result['missing_planned_data'] is True
        assert result['reason'] == 'No pre-registrations found'

    def test_primary_priority(self, mocker):
        mock_data = {
            'pre_registrations': [
                {'title': 'Secondary Registration', 'data': {'description': 'Secondary'}},
                {'title': 'Primary Pre-registration', 'data': {'description': 'Primary'}}
            ]
        }
        mocker.patch('code.extraction.get_study_metadata', return_value=mock_data)
        result = fetch_study_pre_registration_data("fake-id-456")
        
        assert result['missing_planned_data'] is False
        assert 'Primary' in result['primary_content']

    def test_content_extraction_failure(self, mocker):
        mock_data = {
            'pre_registrations': [
                {'title': 'Empty Reg', 'data': {}}
            ]
        }
        mocker.patch('code.extraction.get_study_metadata', return_value=mock_data)
        result = fetch_study_pre_registration_data("fake-id-789")
        
        assert result['missing_planned_data'] is True
        assert result['reason'] == 'Pre-registration content not accessible or empty'
