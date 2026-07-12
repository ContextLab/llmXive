"""
Unit Tests for Framing Validator Module (T028)

Tests verify that:
1. Causal verbs are correctly detected
2. Associational language passes validation
3. Context and line numbers are accurate
4. Validation report generation works correctly
"""
import pytest
from pathlib import Path
import tempfile
import os

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.framing_validator import (
    load_report_text,
    find_causal_phrases,
    validate_report,
    generate_validation_report,
    CAUSAL_VERBS
)


class TestLoadReportText:
    """Tests for load_report_text function."""
    
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing report file."""
        report_file = tmp_path / "test_report.md"
        content = "This is a test report."
        report_file.write_text(content)
        
        result = load_report_text(report_file)
        assert result == content
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading a non-existent file raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.md"
        
        with pytest.raises(FileNotFoundError):
            load_report_text(nonexistent)
    
    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file."""
        report_file = tmp_path / "empty.md"
        report_file.write_text("")
        
        result = load_report_text(report_file)
        assert result == ""


class TestFindCausalPhrases:
    """Tests for find_causal_phrases function."""
    
    def test_detect_causes(self):
        """Test detection of 'causes'."""
        text = "Social exclusion causes reduced activation."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['phrase'] == 'causes'
        assert findings[0]['line'] == 1
    
    def test_detect_leads_to(self):
        """Test detection of 'leads to'."""
        text = "Exclusion leads to lower reward response."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['phrase'] == 'leads to'
    
    def test_detect_results_in(self):
        """Test detection of 'results in'."""
        text = "The manipulation results in significant differences."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['phrase'] == 'results in'
    
    def test_detect_induces(self):
        """Test detection of 'induces'."""
        text = "Social pain induces neural changes."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['phrase'] == 'induces'
    
    def test_detect_forces(self):
        """Test detection of 'forces'."""
        text = "Exclusion forces the brain to adapt."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['phrase'] == 'forces'
    
    def test_no_causal_language(self):
        """Test that associational language passes without findings."""
        text = "Social exclusion is associated with reduced activation."
        findings = find_causal_phrases(text)
        
        assert len(findings) == 0
    
    def test_multiple_findings(self):
        """Test detection of multiple causal phrases."""
        text = """Exclusion causes pain.
        This leads to reduced activity.
        The result is significant."""
        
        findings = find_causal_phrases(text)
        
        assert len(findings) >= 2  # 'causes' and 'leads to'
    
    def test_line_number_accuracy(self):
        """Test that line numbers are reported correctly."""
        text = """Line 1: No causal language here.
        Line 2: This causes issues.
        Line 3: Also fine."""
        
        findings = find_causal_phrases(text)
        
        assert len(findings) == 1
        assert findings[0]['line'] == 2
    
    def test_context_generation(self):
        """Test that context is generated correctly."""
        text = "Social exclusion causes reduced ventral striatum activation."
        findings = find_causal_phrases(text)
        
        assert 'context' in findings[0]
        assert 'causes' in findings[0]['context']
        assert 'exclusion' in findings[0]['context']
        assert 'activation' in findings[0]['context']


class TestValidateReport:
    """Tests for validate_report function."""
    
    def test_validate_pass(self, tmp_path):
        """Test validation passes with no causal language."""
        report_file = tmp_path / "pass.md"
        report_file.write_text(
            "Social exclusion is associated with reduced activation. "
            "There is a correlation between groups."
        )
        
        result = validate_report(report_file)
        
        assert result['valid'] is True
        assert result['total_findings'] == 0
    
    def test_validate_fail(self, tmp_path):
        """Test validation fails with causal language."""
        report_file = tmp_path / "fail.md"
        report_file.write_text(
            "Social exclusion causes reduced activation. "
            "This leads to significant differences."
        )
        
        result = validate_report(report_file)
        
        assert result['valid'] is False
        assert result['total_findings'] >= 2
    
    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation handles missing files gracefully."""
        nonexistent = tmp_path / "missing.md"
        
        result = validate_report(nonexistent)
        
        assert result['valid'] is False
        assert 'error' in result


class TestGenerateValidationReport:
    """Tests for generate_validation_report function."""
    
    def test_report_generation(self):
        """Test that a validation report is generated."""
        result = {
            'valid': False,
            'total_findings': 1,
            'findings': [{
                'phrase': 'causes',
                'line': 1,
                'context': 'exclusion causes activation',
                'suggestion': 'is associated with'
            }],
            'summary': 'Found 1 violation'
        }
        
        report = generate_validation_report(result)
        
        assert 'FRAMING VALIDATION REPORT' in report
        assert 'causes' in report
        assert 'is associated with' in report
    
    def test_report_to_file(self, tmp_path):
        """Test saving report to file."""
        result = {
            'valid': True,
            'total_findings': 0,
            'findings': [],
            'summary': 'No violations'
        }
        
        output_path = tmp_path / "validation_report.txt"
        report = generate_validation_report(result, output_path)
        
        assert output_path.exists()
        assert 'FRAMING VALIDATION REPORT' in output_path.read_text()
        assert report == output_path.read_text()


class TestIntegration:
    """Integration tests for the full validation workflow."""
    
    def test_full_workflow_pass(self, tmp_path):
        """Test complete validation workflow with passing report."""
        report_file = tmp_path / "summary_report.md"
        report_file.write_text(
            "# Summary Report\n\n"
            "Social exclusion is associated with reduced ventral striatum activation.\n"
            "There is a correlation between exclusion and reward response.\n"
        )
        
        result = validate_report(report_file)
        assert result['valid'] is True
    
    def test_full_workflow_fail(self, tmp_path):
        """Test complete validation workflow with failing report."""
        report_file = tmp_path / "summary_report.md"
        report_file.write_text(
            "# Summary Report\n\n"
            "Social exclusion causes reduced ventral striatum activation.\n"
            "This leads to significant behavioral changes.\n"
        )
        
        result = validate_report(report_file)
        assert result['valid'] is False
        assert result['total_findings'] >= 2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])