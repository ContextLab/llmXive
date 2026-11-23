import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from research.populate_research_md import (
    load_json_file,
    read_text_file,
    validate_power_calculation_json,
    validate_citations_json,
    validate_citation_log,
    populate_research_md
)

class TestLoadJsonFile:
    def test_load_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = f.name
        
        try:
            data = load_json_file(temp_path)
            assert data == {"key": "value"}
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_json_file("nonexistent_file.json")

class TestReadTextFile:
    def test_read_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello, world!")
            temp_path = f.name
        
        try:
            content = read_text_file(temp_path)
            assert content == "Hello, world!"
        finally:
            os.unlink(temp_path)
    
    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            read_text_file("nonexistent_file.txt")

class TestValidatePowerCalculationJson:
    def test_valid_power_calculation(self):
        data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "target_power": 0.80,
            "required_n": 128,
            "calculated_n": 128
        }
        assert validate_power_calculation_json(data) is True
    
    def test_missing_field(self):
        data = {
            "effect_size": 0.25,
            "alpha": 0.05,
            "target_power": 0.80
        }
        assert validate_power_calculation_json(data) is False

class TestValidateCitationsJson:
    def test_valid_citations(self):
        data = [
            {
                "title": "Test Title",
                "doi": "10.1234/test",
                "overlap_score": 0.85,
                "status": "valid"
            }
        ]
        assert validate_citations_json(data) is True
    
    def test_empty_list(self):
        assert validate_citations_json([]) is False
    
    def test_missing_field(self):
        data = [
            {
                "title": "Test Title",
                "doi": "10.1234/test"
            }
        ]
        assert validate_citations_json(data) is False

class TestValidateCitationLog:
    def test_valid_log(self):
        content = """# Citation Verification Log
        ## Summary
        - **Test Title**
          - Status: valid
        ## Overall Status
        Status: valid"""
        assert validate_citation_log(content) is True
    
    def test_invalid_log(self):
        content = "Some random text"
        assert validate_citation_log(content) is False

class TestPopulateResearchMd:
    def test_populate_research_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create power calculation file
            power_path = os.path.join(tmpdir, "power_calculation.json")
            with open(power_path, 'w') as f:
                json.dump({
                    "effect_size": 0.25,
                    "alpha": 0.05,
                    "target_power": 0.80,
                    "required_n": 128,
                    "calculated_n": 128
                }, f)
            
            # Create validation report
            validation_path = os.path.join(tmpdir, "validation_report.json")
            with open(validation_path, 'w') as f:
                json.dump([
                    {
                        "title": "Test Title",
                        "doi": "10.1234/test",
                        "overlap_score": 0.85,
                        "status": "valid"
                    }
                ], f)
            
            # Create citation log
            log_path = os.path.join(tmpdir, "citation_verification_log.md")
            with open(log_path, 'w') as f:
                f.write("""# Citation Verification Log
                ## Summary
                - **Test Title**
                  - Status: valid
                ## Overall Status
                Status: valid""")
            
            # Create research.md template
            output_path = os.path.join(tmpdir, "research.md")
            with open(output_path, 'w') as f:
                f.write("""# Research Plan

                ## Power Analysis

                | Effect Size | Alpha | Target Power | Required N | Calculated N |
                |-------------|-------|--------------|------------|--------------|
                | 0.25        | 0.05  | 0.80         | TBD        | TBD          |
                """)
            
            # Run the population function
            populate_research_md(power_path, validation_path, log_path, output_path)
            
            # Verify the output
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "| 0.25 | 0.05 | 0.80 | 128 | 128 |" in content
            assert "TBD" not in content