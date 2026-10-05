"""
Unit tests for metrics calculation functions in code/metrics.py.

Specifically tests V/100LOC (Vulnerability Density) calculation logic.
"""
import pytest
import pandas as pd
import os
import sys
import tempfile
from pathlib import Path

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics import calculate_vuln_density, process_findings_csv, load_severity_map


class TestCalculateVulnDensity:
    """Tests for the calculate_vuln_density function."""

    def test_basic_vuln_density_calculation(self):
        """Test standard calculation: vulns / (LOC / 100)."""
        vuln_count = 5
        line_count = 200
        
        result = calculate_vuln_density(vuln_count, line_count)
        
        # Expected: 5 / (200/100) = 5 / 2 = 2.5
        expected = 2.5
        assert result == expected, f"Expected {expected}, got {result}"

    def test_vuln_density_zero_lines(self):
        """Test handling of zero line count (division by zero protection)."""
        vuln_count = 3
        line_count = 0
        
        # Should return 0.0 or raise a specific error, but not crash with ZeroDivisionError
        # Based on standard metric definitions, density on 0 LOC is 0
        result = calculate_vuln_density(vuln_count, line_count)
        assert result == 0.0, "Density for 0 LOC should be 0.0"

    def test_vuln_density_no_vulnerabilities(self):
        """Test calculation when there are no vulnerabilities."""
        vuln_count = 0
        line_count = 150
        
        result = calculate_vuln_density(vuln_count, line_count)
        expected = 0.0
        assert result == expected, f"Expected {expected}, got {result}"

    def test_vuln_density_large_dataset(self):
        """Test calculation with larger numbers to ensure precision."""
        vuln_count = 120
        line_count = 50000
        
        result = calculate_vuln_density(vuln_count, line_count)
        # 120 / (50000/100) = 120 / 500 = 0.24
        expected = 0.24
        assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"

    def test_vuln_density_single_line(self):
        """Test calculation on a single line of code."""
        vuln_count = 1
        line_count = 1
        
        result = calculate_vuln_density(vuln_count, line_count)
        # 1 / (1/100) = 100.0
        expected = 100.0
        assert result == expected, f"Expected {expected}, got {result}"


class TestProcessFindingsCSV:
    """Tests for the process_findings_csv function which aggregates metrics."""

    def test_process_findings_basic(self):
        """Test processing a simple CSV with findings and line counts."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("snippet_id,model,prompt_id,vuln_count,line_count\n")
            f.write("s1,modelA,p1,2,100\n")
            f.write("s2,modelA,p2,0,50\n")
            f.write("s3,modelB,p1,5,200\n")
            temp_path = f.name

        try:
            df = process_findings_csv(temp_path)
            
            # Verify columns exist
            assert 'snippet_id' in df.columns
            assert 'model' in df.columns
            assert 'vuln_density' in df.columns
            
            # Verify calculations
            # s1: 2 / (100/100) = 2.0
            # s2: 0 / (50/100) = 0.0
            # s3: 5 / (200/100) = 2.5
            
            assert df.loc[df['snippet_id'] == 's1', 'vuln_density'].iloc[0] == 2.0
            assert df.loc[df['snippet_id'] == 's2', 'vuln_density'].iloc[0] == 0.0
            assert df.loc[df['snippet_id'] == 's3', 'vuln_density'].iloc[0] == 2.5
            
        finally:
            os.unlink(temp_path)

    def test_process_findings_zero_loc_handling(self):
        """Test that rows with 0 LOC are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("snippet_id,model,prompt_id,vuln_count,line_count\n")
            f.write("s1,modelA,p1,1,0\n")
            temp_path = f.name

        try:
            df = process_findings_csv(temp_path)
            # Should not crash, density should be 0.0
            assert df.loc[df['snippet_id'] == 's1', 'vuln_density'].iloc[0] == 0.0
        finally:
            os.unlink(temp_path)


class TestLoadSeverityMap:
    """Tests for loading the NIST severity map configuration."""

    def test_load_severity_map_exists(self):
        """Test that the function can load the standard severity map file."""
        # The map should exist at the expected path based on T007
        map_path = Path(__file__).parent.parent.parent / "data" / "mappings" / "nist_severity_map.yaml"
        
        if map_path.exists():
            result = load_severity_map(str(map_path))
            assert isinstance(result, dict), "Severity map should be a dictionary"
            assert len(result) > 0, "Severity map should not be empty"
        else:
            # If the file doesn't exist yet (e.g., T007 not run), skip or assert failure
            # For robust testing, we might want to create a temp one, but here we check existence
            pytest.skip("nist_severity_map.yaml not found; T007 may not be completed.")

    def test_load_severity_map_invalid_file(self):
        """Test handling of invalid YAML files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("not: valid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises((yaml.YAMLError, Exception)):
                load_severity_map(temp_path)
        finally:
            os.unlink(temp_path)