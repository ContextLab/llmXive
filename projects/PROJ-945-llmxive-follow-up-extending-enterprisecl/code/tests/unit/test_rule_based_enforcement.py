import json
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modeling.verify_rule_based_enforcement import (
    load_dataset_records, 
    check_for_manual_labels, 
    run_enforcement_check
)

class TestRuleBasedEnforcement:
    
    def test_load_dataset_records_success(self):
        """Test loading a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "status": "success"}\n')
            f.write('{"id": 2, "status": "failure"}\n')
            temp_path = f.name
        
        try:
            records = load_dataset_records(temp_path)
            assert len(records) == 2
            assert records[0]['id'] == 1
            assert records[1]['status'] == 'failure'
        finally:
            os.unlink(temp_path)

    def test_load_dataset_records_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_dataset_records("non_existent_file.jsonl")

    def test_load_dataset_records_invalid_json(self):
        """Test that ValueError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('not valid json\n')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_dataset_records(temp_path)
        finally:
            os.unlink(temp_path)

    def test_check_for_manual_labels_clean(self):
        """Test that no findings are returned for clean data."""
        records = [
            {"id": 1, "label": "rule_based", "error_type": "syntax"},
            {"id": 2, "label": "rule_based", "error_type": "token_mismatch"}
        ]
        findings = check_for_manual_labels(records)
        assert len(findings) == 0

    def test_check_for_manual_labels_manual_field(self):
        """Test detection of explicit manual label fields."""
        records = [
            {"id": 1, "manual_label": "human_fixed"},
            {"id": 2, "human_annotation": "expert_reviewed"}
        ]
        findings = check_for_manual_labels(records)
        assert len(findings) == 2
        assert any(f['field_name'] == 'manual_label' for f in findings)
        assert any(f['field_name'] == 'human_annotation' for f in findings)

    def test_check_for_manual_labels_label_source(self):
        """Test detection of label_source == 'manual'."""
        records = [
            {"id": 1, "label": "auto", "label_source": "rule_engine"},
            {"id": 2, "label": "auto", "label_source": "manual"}
        ]
        findings = check_for_manual_labels(records)
        assert len(findings) == 1
        assert findings[0]['field_name'] == 'label_source'
        assert findings[0]['value'] == 'manual'

    def test_run_enforcement_check_pass(self):
        """Test successful run with no manual labels."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "label": "auto"}\n')
            input_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            report = run_enforcement_check(input_path, output_path)
            assert report['status'] == 'pass'
            assert report['manual_labels_found'] is False
            
            # Verify file written
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report['status'] == 'pass'
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_run_enforcement_check_fail(self):
        """Test that RuntimeError is raised when manual labels are found."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "manual_label": "human"}\n')
            input_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            with pytest.raises(RuntimeError) as excinfo:
                run_enforcement_check(input_path, output_path)
            
            assert "manual label instances detected" in str(excinfo.value)
            
            # Verify failure report written
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report['status'] == 'fail'
            assert saved_report['manual_labels_found'] is True
        finally:
            os.unlink(input_path)
            os.unlink(output_path)