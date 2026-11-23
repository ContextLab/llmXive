import os
import csv
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, 'code')

from validate_spot_check import (
    generate_annotation_template,
    load_processed_data,
    load_annotations,
    calculate_false_negative_rate,
    handle_missing_annotations,
    DataValidationError
)

class TestGenerateAnnotationTemplate:
    def test_template_generation_creates_file(self, tmp_path):
        """Test that generate_annotation_template creates the output file."""
        processed_data = [
            {"pr_id": 1, "is_ai_assisted": "0", "repo_name": "test/repo1"},
            {"pr_id": 2, "is_ai_assisted": "1", "repo_name": "test/repo2"},
            {"pr_id": 3, "is_ai_assisted": "0", "repo_name": "test/repo3"}
        ]
        
        output_path = tmp_path / "annotation_template.csv"
        generate_annotation_template(processed_data, str(output_path))
        
        assert output_path.exists(), "Annotation template file was not created."
    
    def test_template_contains_instructions(self, tmp_path):
        """Test that the template contains the required header instructions."""
        processed_data = [
            {"pr_id": 1, "is_ai_assisted": "0"}
        ]
        output_path = tmp_path / "annotation_template.csv"
        generate_annotation_template(processed_data, str(output_path))
        
        content = output_path.read_text()
        
        assert "# ANNOTATION TEMPLATE" in content
        assert "Instructions for Human Annotator:" in content
        assert "copilot" in content.lower()
        assert "ai-generated" in content.lower()
        assert "Save the file as 'annotations.csv'" in content
    
    def test_template_excludes_ai_assisted_prs(self, tmp_path):
        """Test that PRs already labeled as AI-assisted are excluded from the template."""
        processed_data = [
            {"pr_id": 1, "is_ai_assisted": "0"},
            {"pr_id": 2, "is_ai_assisted": "1"},
            {"pr_id": 3, "is_ai_assisted": "0"}
        ]
        
        output_path = tmp_path / "annotation_template.csv"
        generate_annotation_template(processed_data, str(output_path))
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        pr_ids = [int(row['pr_id']) for row in rows]
        
        assert 1 in pr_ids
        assert 3 in pr_ids
        assert 2 not in pr_ids  # AI-assisted should be excluded
    
    def test_template_has_correct_columns(self, tmp_path):
        """Test that the template has the correct column headers."""
        processed_data = [{"pr_id": 1, "is_ai_assisted": "0"}]
        output_path = tmp_path / "annotation_template.csv"
        generate_annotation_template(processed_data, str(output_path))
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            # Skip comment lines if present in DictReader logic (it usually ignores them)
            # We check the fieldnames
            fieldnames = reader.fieldnames
        
        assert 'pr_id' in fieldnames
        assert 'is_ai_assisted' in fieldnames

class TestCalculateFalseNegativeRate:
    def test_correct_fnr_calculation(self):
        """Test calculation of false negative rate."""
        automated_data = [
            {"pr_id": 1, "is_ai_assisted": "0"}, # FN if human says 1
            {"pr_id": 2, "is_ai_assisted": "0"}, # TN if human says 0
            {"pr_id": 3, "is_ai_assisted": "1"}, # TP
            {"pr_id": 4, "is_ai_assisted": "0"}  # FN if human says 1
        ]
        
        human_annotations = [
            {"pr_id": 1, "is_ai_assisted": 1}, # FN
            {"pr_id": 2, "is_ai_assisted": 0}, # TN
            {"pr_id": 3, "is_ai_assisted": 1}, # TP
            {"pr_id": 4, "is_ai_assisted": 1}  # FN
        ]
        
        fnr = calculate_false_negative_rate(automated_data, human_annotations)
        
        # Total negatives (auto=0) = 3 (ids 1, 2, 4)
        # False negatives (auto=0, human=1) = 2 (ids 1, 4)
        # FNR = 2/3
        assert abs(fnr - 2/3) < 0.0001
    
    def test_zero_negatives_returns_zero(self):
        """Test that if there are no negatives, FNR is 0."""
        automated_data = [
            {"pr_id": 1, "is_ai_assisted": "1"}
        ]
        human_annotations = [
            {"pr_id": 1, "is_ai_assisted": 1}
        ]
        
        fnr = calculate_false_negative_rate(automated_data, human_annotations)
        assert fnr == 0.0

class TestHandleMissingAnnotations:
    def test_creates_status_file(self, tmp_path):
        """Test that handle_missing_annotations creates the status file."""
        status_path = tmp_path / "validation_status.json"
        handle_missing_annotations(str(status_path))
        
        assert status_path.exists()
        
        with open(status_path, 'r') as f:
            status = json.load(f)
        
        assert status["status"] == "UNVALIDATED"
        assert status["rate"] is None
        assert "missing" in status["message"].lower()