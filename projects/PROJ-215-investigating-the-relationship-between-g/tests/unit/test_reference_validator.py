import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from code.reference_validator import validate_url_access, run_reference_validation

class TestValidateUrlAccess:
    def test_validate_url_access_success(self):
        """Test successful URL access validation"""
        with patch('code.reference_validator.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_head.return_value = mock_response
            
            result = validate_url_access("https://example.com")
            
            assert result["accessible"] is True
            assert result["status_code"] == 200
            assert "error" not in result

    def test_validate_url_access_404(self):
        """Test URL access validation with 404 error"""
        with patch('code.reference_validator.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            result = validate_url_access("https://example.com/notfound")
            
            assert result["accessible"] is False
            assert result["status_code"] == 404
            assert "error" in result

    def test_validate_url_access_timeout(self):
        """Test URL access validation with timeout"""
        with patch('code.reference_validator.requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection timeout")
            
            result = validate_url_access("https://example.com")
            
            assert result["accessible"] is False
            assert "error" in result

class TestRunReferenceValidation:
    def test_run_reference_validation_single_cohort(self):
        """Test validation of a single cohort"""
        cohorts = [
            {
                "name": "Test Cohort",
                "url": "https://example.com",
                "description": "Test description",
                "type": "cohort"
            }
        ]
        
        with patch('code.reference_validator.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            result = run_reference_validation(cohorts)
            
            assert result["total_cohorts"] == 1
            assert result["accessible_count"] == 1
            assert result["inaccessible_count"] == 0
            assert len(result["details"]) == 1
            assert result["details"][0]["name"] == "Test Cohort"
            assert result["details"][0]["accessible"] is True

    def test_run_reference_validation_mixed_results(self):
        """Test validation with mixed accessible/inaccessible cohorts"""
        cohorts = [
            {
                "name": "Accessible Cohort",
                "url": "https://example.com/ok",
                "description": "Should be accessible",
                "type": "cohort"
            },
            {
                "name": "Inaccessible Cohort",
                "url": "https://example.com/missing",
                "description": "Should be inaccessible",
                "type": "cohort"
            }
        ]
        
        with patch('code.reference_validator.requests.head') as mock_head:
            # First call succeeds, second fails
            mock_response_ok = MagicMock()
            mock_response_ok.status_code = 200
            
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 404
            
            mock_head.side_effect = [mock_response_ok, mock_response_fail]
            
            result = run_reference_validation(cohorts)
            
            assert result["total_cohorts"] == 2
            assert result["accessible_count"] == 1
            assert result["inaccessible_count"] == 1
            
            # Verify order is preserved
            assert result["details"][0]["name"] == "Accessible Cohort"
            assert result["details"][0]["accessible"] is True
            assert result["details"][1]["name"] == "Inaccessible Cohort"
            assert result["details"][1]["accessible"] is False
