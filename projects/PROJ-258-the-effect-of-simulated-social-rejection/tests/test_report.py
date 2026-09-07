import pytest
import json
import os
import tempfile
from code.report import generate_report_logic, verify_report_constraints, save_report

def test_generate_report_logic_injects_associational():
    """
    Test that the generated report contains the phrase 'associational'
    and excludes 'causal' in the Results section.
    """
    mock_results = {
        "p_value": 0.03,
        "f_statistic": 4.5,
        "effect_size": 0.8,
        "n_subjects": 50,
        "sensitivity_results": {
            0.01: {"significant": False, "p_value": 0.03},
            0.05: {"significant": True, "p_value": 0.03},
            0.10: {"significant": True, "p_value": 0.03}
        }
    }
    
    report_content = generate_report_logic(mock_results, "Within-Subjects")
    
    # Check for 'associational'
    assert "associational" in report_content.lower(), "Report must contain 'associational'."
    
    # Check for 'causal' exclusion in Results
    # Split the report to find the Results section
    if "## 3. Results" in report_content:
        results_section = report_content.split("## 3. Results")[1].split("## 4.")[0]
        assert "causal" not in results_section.lower(), "Report must not contain 'causal' in Results section."
    
    # Check for sensitivity table
    assert "| Alpha Level |" in report_content, "Report must contain sensitivity table header."
    assert "0.01" in report_content, "Report must contain alpha 0.01."
    assert "0.05" in report_content, "Report must contain alpha 0.05."
    assert "0.1" in report_content or "0.10" in report_content, "Report must contain alpha 0.10."

def test_verify_report_constraints():
    """
    Test the verify_report_constraints function with a valid report.
    """
    # Create a temporary file with valid content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""
        # Test Report
        ## 3. Results
        Some results here.
        ## 5. Limitations
        This study is associational. No causal claims can be made.
        """)
        temp_path = f.name
    
    try:
        assert verify_report_constraints(temp_path) == True, "Valid report should pass verification."
    finally:
        os.unlink(temp_path)

def test_verify_report_constraints_fails_on_causal_in_results():
    """
    Test that verify_report_constraints fails if 'causal' is in Results.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""
        # Test Report
        ## 3. Results
        This proves a causal link.
        ## 5. Limitations
        This study is associational.
        """)
        temp_path = f.name
    
    try:
        assert verify_report_constraints(temp_path) == False, "Report with 'causal' in Results should fail."
    finally:
        os.unlink(temp_path)

def test_verify_report_constraints_fails_on_missing_associational():
    """
    Test that verify_report_constraints fails if 'associational' is missing.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""
        # Test Report
        ## 3. Results
        Results here.
        ## 5. Limitations
        This study has limitations.
        """)
        temp_path = f.name
    
    try:
        assert verify_report_constraints(temp_path) == False, "Report without 'associational' should fail."
    finally:
        os.unlink(temp_path)