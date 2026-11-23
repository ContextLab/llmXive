import json
import pytest
from pathlib import Path
from code.research.validate_phase0 import (
    load_json_file,
    read_text_file,
    validate_power_calculation_json,
    validate_citations_json,
    validate_citation_log,
    validate_research_md
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    return research_dir

def test_load_json_file_success(temp_dir):
    """Test loading a valid JSON file."""
    test_file = temp_dir / "test.json"
    test_data = {"key": "value", "number": 42}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    result = load_json_file(test_file)
    assert result == test_data

def test_load_json_file_not_found():
    """Test loading a non-existent JSON file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_json_file(Path("nonexistent.json"))

def test_read_text_file_success(temp_dir):
    """Test reading a valid text file."""
    test_file = temp_dir / "test.txt"
    test_content = "Hello, World!\nLine 2"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    result = read_text_file(test_file)
    assert result == test_content

def test_read_text_file_not_found():
    """Test reading a non-existent text file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_text_file(Path("nonexistent.txt"))

def test_validate_power_calculation_json_valid():
    """Test validation with valid power calculation data."""
    valid_data = {
        "effect_size": 0.25,
        "alpha": 0.05,
        "target_power": 0.80,
        "required_n": 128,
        "calculated_n": 128,
        "test_type": "anova"
    }
    errors = validate_power_calculation_json(valid_data)
    assert len(errors) == 0

def test_validate_power_calculation_json_missing_keys():
    """Test validation with missing required keys."""
    invalid_data = {
        "effect_size": 0.25,
        "alpha": 0.05
    }
    errors = validate_power_calculation_json(invalid_data)
    assert len(errors) > 0
    assert any("Missing required key" in error for error in errors)

def test_validate_power_calculation_json_invalid_n():
    """Test validation with invalid N values."""
    invalid_data = {
        "effect_size": 0.25,
        "alpha": 0.05,
        "target_power": 0.80,
        "required_n": -10,
        "calculated_n": 0,
        "test_type": "anova"
    }
    errors = validate_power_calculation_json(invalid_data)
    assert len(errors) >= 2  # Both required_n and calculated_n should fail

def test_validate_citations_json_valid():
    """Test validation with valid citation data."""
    valid_data = [
        {
            "title": "Trust in Automation",
            "doi": "10.1234/example",
            "overlap_score": 0.85,
            "status": "valid"
        }
    ]
    errors = validate_citations_json(valid_data)
    assert len(errors) == 0

def test_validate_citations_json_invalid_score():
    """Test validation with invalid overlap score."""
    invalid_data = [
        {
            "title": "Example",
            "doi": "10.1234/example",
            "overlap_score": 1.5,
            "status": "valid"
        }
    ]
    errors = validate_citations_json(invalid_data)
    assert len(errors) > 0
    assert any("overlap_score must be between 0 and 1" in error for error in errors)

def test_validate_citation_log_valid():
    """Test validation with valid citation log content."""
    valid_content = """
    ## Citation Verification Results
    
    | Citation | Status |
    |----------|--------|
    | Lee & See (2004) | status=valid |
    | Langer (1975) | status=valid |
    """
    errors = validate_citation_log(valid_content)
    assert len(errors) == 0

def test_validate_citation_log_empty():
    """Test validation with empty log content."""
    errors = validate_citation_log("")
    assert len(errors) > 0
    assert any("empty" in error.lower() for error in errors)

def test_validate_research_md_valid(temp_dir):
    """Test validation with valid research.md content."""
    valid_content = """
    # Research Plan
    
    ## Power Analysis Results
    
    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    |-------------|-------|--------------|------------|--------------|
    | 0.25        | 0.05  | 0.80         | 128        | 128          |
    
    ## Conclusion
    
    The power analysis indicates that 128 participants are required.
    """
    power_data = {
        "effect_size": 0.25,
        "alpha": 0.05,
        "target_power": 0.80,
        "required_n": 128,
        "calculated_n": 128,
        "test_type": "anova"
    }
    errors = validate_research_md(valid_content, power_data)
    assert len(errors) == 0

def test_validate_research_md_missing_table():
    """Test validation with missing table headers."""
    invalid_content = """
    # Research Plan
    
    Some text without a table.
    """
    errors = validate_research_md(invalid_content, {})
    assert len(errors) > 0
    assert any("Missing table header" in error for error in errors)

def test_validate_research_md_no_data_rows():
    """Test validation with table but no data rows."""
    invalid_content = """
    # Research Plan
    
    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    |-------------|-------|--------------|------------|--------------|
    """
    errors = validate_research_md(invalid_content, {})
    assert len(errors) > 0
    assert any("no data rows" in error.lower() for error in errors)
