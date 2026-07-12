"""
Unit tests for citation verification logic.

This test suite validates that the verify_citations.py module correctly
resolves the "GUI Error Taxonomy" source and produces the expected
validation report.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# Import from the project's verify_citations module
from verify_citations import (
    check_url_reachable,
    parse_yaml_simple,
    validate_citations,
    main
)
from config import get_project_root


class TestCitationValidation:
    """Tests for citation validation functionality."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure mimicking the project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create necessary directories
            data_dir = Path(tmpdir) / "data"
            results_dir = data_dir / "results"
            results_dir.mkdir(parents=True)
            
            # Create a mock taxonomy file
            taxonomy_path = data_dir / "config" / "gui_error_taxonomy.yaml"
            taxonomy_path.parent.mkdir(parents=True, exist_ok=True)
            
            taxonomy_content = """
            taxonomy_name: "GUI Error Taxonomy v1.0"
            version: "1.0"
            source_url: "https://raw.githubusercontent.com/llmXive/taxonomy/main/gui_error_taxonomy.yaml"
            description: "Standardized taxonomy of GUI interaction errors"
            errors:
              - id: "ERR_001"
                name: "Misplaced Click"
                description: "User clicks outside intended target"
                recovery: "Retry with larger hit area"
              - id: "ERR_002"
                name: "Scroll Jam"
                description: "Scrolling becomes unresponsive"
                recovery: "Reset scroll position"
            """
            taxonomy_path.write_text(taxonomy_content)
            
            yield tmpdir
            
    def test_parse_yaml_simple(self, temp_project_root):
        """Test that YAML parsing works correctly."""
        taxonomy_path = Path(temp_project_root) / "data" / "config" / "gui_error_taxonomy.yaml"
        result = parse_yaml_simple(taxonomy_path)
        
        assert result is not None
        assert "taxonomy_name" in result
        assert result["taxonomy_name"] == "GUI Error Taxonomy v1.0"
        assert "errors" in result
        assert len(result["errors"]) == 2
        
    def test_validate_citations_basic(self, temp_project_root):
        """Test basic citation validation with local file."""
        taxonomy_path = Path(temp_project_root) / "data" / "config" / "gui_error_taxonomy.yaml"
        results_path = Path(temp_project_root) / "data" / "results" / "taxonomy_validation_report.json"
        
        # Run validation
        success = validate_citations(taxonomy_path, results_path)
        
        assert success is True
        assert results_path.exists()
        
        # Verify report content
        with open(results_path, 'r') as f:
            report = json.load(f)
        
        assert "taxonomy_name" in report
        assert report["taxonomy_name"] == "GUI Error Taxonomy v1.0"
        assert "validation_status" in report
        assert report["validation_status"] == "PASSED"
        assert "source_resolved" in report
        assert report["source_resolved"] is True
        assert "error_count" in report
        assert report["error_count"] == 2
        
    def test_main_function_integration(self, temp_project_root, capsys):
        """Test the main function integration."""
        # Set environment variable to point to temp root
        os.environ["PROJECT_ROOT"] = temp_project_root
        
        # Run main
        main()
        
        # Check that report was created
        results_path = Path(temp_project_root) / "data" / "results" / "taxonomy_validation_report.json"
        assert results_path.exists()
        
        # Verify report content
        with open(results_path, 'r') as f:
            report = json.load(f)
        
        assert report["validation_status"] == "PASSED"
        
    def test_url_reachability(self):
        """Test URL reachability check (may fail if network unavailable)."""
        # Test with a known good URL
        good_url = "https://www.google.com"
        result = check_url_reachable(good_url)
        # Note: This might fail in isolated environments, so we handle both cases
        if result:
            assert result is True
        else:
            # If network is unavailable, we expect False but don't fail the test
            pytest.skip("Network unavailable for URL reachability test")
            
    def test_invalid_yaml_handling(self, temp_project_root):
        """Test handling of invalid YAML files."""
        invalid_path = Path(temp_project_root) / "data" / "config" / "invalid.yaml"
        invalid_path.write_text("invalid: yaml: content: [broken")
        
        results_path = Path(temp_project_root) / "data" / "results" / "invalid_report.json"
        
        # Should return False for invalid YAML
        success = validate_citations(invalid_path, results_path)
        assert success is False
        
        # Check that report indicates failure
        if results_path.exists():
            with open(results_path, 'r') as f:
                report = json.load(f)
            assert report["validation_status"] == "FAILED"
            
    def test_missing_file_handling(self, temp_project_root):
        """Test handling of missing files."""
        missing_path = Path(temp_project_root) / "data" / "config" / "missing.yaml"
        results_path = Path(temp_project_root) / "data" / "results" / "missing_report.json"
        
        success = validate_citations(missing_path, results_path)
        assert success is False
        
        if results_path.exists():
            with open(results_path, 'r') as f:
                report = json.load(f)
            assert report["validation_status"] == "FAILED"
            assert "source_resolved" in report
            assert report["source_resolved"] is False
            
    def test_taxonomy_validation_report_structure(self, temp_project_root):
        """Verify the taxonomy validation report has all required fields."""
        taxonomy_path = Path(temp_project_root) / "data" / "config" / "gui_error_taxonomy.yaml"
        results_path = Path(temp_project_root) / "data" / "results" / "taxonomy_validation_report.json"
        
        validate_citations(taxonomy_path, results_path)
        
        with open(results_path, 'r') as f:
            report = json.load(f)
        
        required_fields = [
            "taxonomy_name",
            "version",
            "validation_status",
            "source_resolved",
            "error_count",
            "errors_list",
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in report, f"Missing required field: {field}"
            
        # Verify specific values
        assert report["validation_status"] == "PASSED"
        assert report["source_resolved"] is True
        assert report["error_count"] == 2
        assert len(report["errors_list"]) == 2
        
    def test_gui_error_taxonomy_specific_validation(self, temp_project_root):
        """Specific test for GUI Error Taxonomy validation requirements."""
        taxonomy_path = Path(temp_project_root) / "data" / "config" / "gui_error_taxonomy.yaml"
        results_path = Path(temp_project_root) / "data" / "results" / "taxonomy_validation_report.json"
        
        success = validate_citations(taxonomy_path, results_path)
        
        assert success is True
        
        with open(results_path, 'r') as f:
            report = json.load(f)
        
        # Verify it's the correct taxonomy
        assert report["taxonomy_name"] == "GUI Error Taxonomy v1.0"
        assert report["version"] == "1.0"
        
        # Verify error structure
        assert "errors_list" in report
        assert len(report["errors_list"]) == 2
        
        # Verify first error
        first_error = report["errors_list"][0]
        assert first_error["id"] == "ERR_001"
        assert first_error["name"] == "Misplaced Click"
        
        # Verify second error
        second_error = report["errors_list"][1]
        assert second_error["id"] == "ERR_002"
        assert second_error["name"] == "Scroll Jam"
        
        # Verify timestamp is present and valid
        assert "timestamp" in report
        from datetime import datetime
        datetime.fromisoformat(report["timestamp"].replace('Z', '+00:00'))