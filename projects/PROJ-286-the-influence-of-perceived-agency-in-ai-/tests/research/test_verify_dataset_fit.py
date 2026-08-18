import pytest
from pathlib import Path
from code.research.verify_dataset_fit import extract_dataset_section, check_variable_definitions, generate_verification_report

def test_extract_dataset_section_found():
    plan_content = """
    # Plan
    Some content
    
    ## Dataset Variable Fit
    - Condition ID: Unique identifier for the experimental condition (High, Low, Control)
    - Adherence Rate: Percentage of AI recommendations followed by the participant
    - Trust Score: Aggregate score from the 12-item Lee & See scale
    - Perceived Agency Score: Self-reported measure of perceived control
    - Attention Check Status: Boolean indicating if attention checks were passed
    
    ## Other Section
    More content
    """
    variables = extract_dataset_section(plan_content)
    assert 'Condition ID' in variables or any('condition' in k.lower() for k in variables.keys())
    assert 'Adherence Rate' in variables or any('adherence' in k.lower() for k in variables.keys())

def test_extract_dataset_section_missing():
    plan_content = """
    # Plan
    Some content without the dataset section
    """
    variables = extract_dataset_section(plan_content)
    assert len(variables) == 0

def test_check_variable_definitions_all_present():
    plan_content = """
    # Plan
    
    ## Dataset Variable Fit
    - Condition ID: Unique identifier for the experimental condition
    - Adherence Rate: Percentage of AI recommendations followed
    - Trust Score: Aggregate score from the 12-item Lee & See scale
    - Perceived Agency Score: Self-reported measure of perceived control
    - Attention Check Status: Boolean indicating if attention checks were passed
    """
    is_verified, missing, found = check_variable_definitions(plan_content)
    assert is_verified is True
    assert len(missing) == 0
    assert len(found) == 5

def test_check_variable_definitions_some_missing():
    plan_content = """
    # Plan
    
    ## Dataset Variable Fit
    - Condition ID: Unique identifier for the experimental condition
    - Trust Score: Aggregate score from the 12-item Lee & See scale
    """
    is_verified, missing, found = check_variable_definitions(plan_content)
    assert is_verified is False
    assert len(missing) == 3  # Adherence Rate, Perceived Agency Score, Attention Check Status
    assert len(found) == 2

def test_generate_verification_report_creates_file(tmp_path):
    output_file = tmp_path / "test_report.md"
    generate_verification_report(True, [], ["Var1"], output_file)
    assert output_file.exists()
    content = output_file.read_text()
    assert "Verified" in content
    assert "Var1" in content
