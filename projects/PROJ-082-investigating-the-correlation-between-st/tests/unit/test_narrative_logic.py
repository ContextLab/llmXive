"""
Unit tests for T015a: Narrative Logic
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from code.analysis.narrative_logic import (
    load_methodology_config,
    load_extracted_studies,
    extract_themes,
    run_narrative_logic
)
from code.utils.config import get_project_root

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_extract_themes_basic(temp_dir):
    """Test basic theme extraction with keywords."""
    # Mock data
    studies = [
        {"author": "Smith", "year": 2020, "tract": "Arcuate", "qualitative_desc": "Increased connectivity in the arcuate fasciculus"},
        {"author": "Jones", "year": 2021, "tract": "Uncinate", "qualitative_desc": "Decreased volume in uncinate fasciculus associated with depression"},
        {"author": "Doe", "year": 2022, "tract": "Cingulum", "qualitative_desc": "No significant findings in cingulum bundle"},
    ]
    
    # Methodology with specific keywords
    methodology = {
        "keywords": ["arcuate", "uncinate", "depression"],
        "sentiment_rules": {},
        "exclusion_criteria": []
    }
    
    result = extract_themes(studies, methodology)
    
    assert result["total_studies_processed"] == 3
    assert "themes" in result
    
    # Check specific theme counts
    # "arcuate" should match study 1
    assert "arcuate" in result["themes"]
    assert result["themes"]["arcuate"]["count"] == 1
    
    # "uncinate" should match study 2
    assert "uncinate" in result["themes"]
    assert result["themes"]["uncinate"]["count"] == 1
    
    # "depression" should match study 2
    assert "depression" in result["themes"]
    assert result["themes"]["depression"]["count"] == 1
    
    # "uncategorized" should match study 3 (no keywords found)
    assert "uncategorized" in result["themes"]
    assert result["themes"]["uncategorized"]["count"] == 1

def test_extract_themes_empty_input():
    """Test extraction with empty study list."""
    studies = []
    methodology = {"keywords": ["test"], "sentiment_rules": {}, "exclusion_criteria": []}
    
    result = extract_themes(studies, methodology)
    
    assert result["total_studies_processed"] == 0
    assert len(result["themes"]) == 0

def test_extract_themes_missing_desc():
    """Test extraction when qualitative_desc is missing or empty."""
    studies = [
        {"author": "Test", "year": 2020, "tract": "Test", "qualitative_desc": ""},
        {"author": "Test2", "year": 2020, "tract": "Test", "qualitative_desc": None},
    ]
    methodology = {"keywords": ["test"], "sentiment_rules": {}, "exclusion_criteria": []}
    
    result = extract_themes(studies, methodology)
    
    # Both should be skipped or counted as uncategorized? 
    # Implementation skips if not desc or not string.
    # If implementation skips, count is 0. If it adds to uncategorized, count is 2.
    # Based on code: `if not desc or not isinstance(desc, str): continue`
    # So they are skipped.
    assert result["total_studies_processed"] == 2
    assert len(result["themes"]) == 0

def test_load_extracted_studies_file_not_found(temp_dir):
    """Test that load_extracted_studies raises error if file missing."""
    fake_path = temp_dir / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_extracted_studies(fake_path)

def test_run_narrative_logic_integration(temp_dir):
    """Integration test for the full run_narrative_logic flow with mocked paths."""
    # Create mock files
    csv_path = temp_dir / "extracted_studies.csv"
    yaml_path = temp_dir / "methodology.yaml"
    output_path = temp_dir / "narrative_themes.json"
    
    # Write mock CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["author", "year", "tract", "qualitative_desc"])
        writer.writeheader()
        writer.writerow({"author": "A", "year": 2020, "tract": "X", "qualitative_desc": "Positive correlation in arcuate"})
    
    # Write mock YAML
    with open(yaml_path, 'w') as f:
        f.write("keywords:\n  - arcuate\n  - positive\n")
    
    # Mock the global paths in the module
    with patch('code.analysis.narrative_logic.EXTRACTED_STUDIES_PATH', csv_path), \
         patch('code.analysis.narrative_logic.METHODOLOGY_CONFIG_PATH', yaml_path), \
         patch('code.analysis.narrative_logic.OUTPUT_PATH', output_path):
        
        result = run_narrative_logic()
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["total_studies_processed"] == 1
        assert "arcuate" in saved_data["themes"]
        assert "positive" in saved_data["themes"]