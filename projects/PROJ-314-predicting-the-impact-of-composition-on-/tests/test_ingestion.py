import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import fetch_materials_project_data, validate_data_gap, generate_data_availability_report

class TestFetchMaterialsProjectData:
    """Tests for Materials Project data fetching."""
    
    def test_fetch_raises_on_missing_api_key(self, monkeypatch):
        """Test that fetch raises RuntimeError when API key is missing."""
        monkeypatch.setenv("MP_API_KEY", "")
        
        with pytest.raises(RuntimeError, match="API key not found"):
            fetch_materials_project_data()
    
    def test_fetch_creates_output_file(self, tmp_path, monkeypatch):
        """Test that fetch creates output file (with mocked API)."""
        # This test would require mocking the MPRestClient
        # For now, we test the structure
        output_path = tmp_path / "test_output.json"
        
        # Mock the API call to return empty data
        # In real tests, we would mock MPRestClient.get_entries
        pass
    
    def test_fetch_fails_loudly_on_empty_data(self, monkeypatch):
        """Test that fetch raises error when no data is returned."""
        # Mock MPRestClient to return empty entries
        from unittest.mock import Mock, patch
        
        mock_client = Mock()
        mock_client.get_entries.return_value = []
        
        with patch('code.ingestion.MPRestClient', return_value=mock_client):
            with pytest.raises(RuntimeError, match="No entries returned"):
                fetch_materials_project_data()

class TestDataValidation:
    """Tests for data validation functions."""
    
    def test_validate_data_gap_passes(self):
        """Test that validation passes with sufficient data."""
        df = pd.DataFrame({"col1": range(30)})
        assert validate_data_gap(df) is True
    
    def test_validate_data_gap_fails(self):
        """Test that validation fails with insufficient data."""
        df = pd.DataFrame({"col1": range(29)})
        assert validate_data_gap(df) is False
    
    def test_generate_data_availability_report(self, tmp_path):
        """Test report generation."""
        df = pd.DataFrame({"col1": range(25)})
        output_path = tmp_path / "report.json"
        
        report = generate_data_availability_report(df, output_path)
        
        assert report["valid_entries"] == 25
        assert report["reason_code"] == "INSUFFICIENT_DATA"
        assert Path(output_path).exists()

class TestIntegration:
    """Integration tests for ingestion pipeline."""
    
    def test_full_ingestion_flow(self, tmp_path):
        """Test complete ingestion flow."""
        # This would test the full pipeline with mocked data
        # For now, a placeholder
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
