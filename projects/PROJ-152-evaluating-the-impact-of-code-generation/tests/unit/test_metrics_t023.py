import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the function we are testing
# We need to mock config or ensure the test runs in an environment where config is valid
# For unit testing, we will pass paths directly or mock the config module if necessary.
# However, the function `calculate_vuln_density` takes DataFrames, so we can test it directly.
# The `main` function relies on config. We will test `calculate_vuln_density` primarily.

# To test `main`, we need to mock file existence or create temp files.

from metrics import calculate_vuln_density, load_severity_map, map_severity_to_ordinal

class TestCalculateVulnDensity:
    def test_basic_calculation(self):
        # Create mock snippets
        snippets_data = {
            "snippet_id": ["s1", "s2", "s3"],
            "model": ["m1", "m1", "m2"],
            "prompt_id": ["p1", "p1", "p2"],
            "line_count": [100, 50, 200]
        }
        snippets_df = pd.DataFrame(snippets_data)
        
        # Create mock findings
        findings_data = {
            "snippet_id": ["s1", "s1", "s3"],
            "severity": ["HIGH", "MEDIUM", "LOW"]
        }
        findings_df = pd.DataFrame(findings_data)
        
        # Mock severity map
        severity_map = {"HIGH": 4, "MEDIUM": 3, "LOW": 2}
        
        # We need to patch the map loading or pass it. 
        # The current implementation of calculate_vuln_density loads the map internally.
        # To test this properly, we need to either:
        # 1. Mock the load_severity_map function
        # 2. Create a temp file for the map and set config
        
        # Let's mock the function for this unit test
        import metrics
        original_load = metrics.load_severity_map
        
        def mock_load(path):
            return severity_map
        
        metrics.load_severity_map = mock_load
        
        try:
            result = calculate_vuln_density(findings_df, snippets_df)
            
            # Check s1: 2 vulns, LOC 100 -> V/100LOC = 2.0
            # Mean severity: (4+3)/2 = 3.5
            s1_row = result[result["snippet_id"] == "s1"].iloc[0]
            assert s1_row["vuln_count"] == 2
            assert s1_row["v_per_100loc"] == 2.0
            assert s1_row["mean_severity"] == 3.5
            
            # Check s2: 0 vulns
            s2_row = result[result["snippet_id"] == "s2"].iloc[0]
            assert s2_row["vuln_count"] == 0
            assert s2_row["v_per_100loc"] == 0.0
            assert s2_row["mean_severity"] == 0.0
            
            # Check s3: 1 vuln, LOC 200 -> V/100LOC = 0.5
            s3_row = result[result["snippet_id"] == "s3"].iloc[0]
            assert s3_row["vuln_count"] == 1
            assert s3_row["v_per_100loc"] == 0.5
            assert s3_row["mean_severity"] == 2.0
            
        finally:
            metrics.load_severity_map = original_load

    def test_zero_lines_of_code(self):
        snippets_data = {
            "snippet_id": ["s1"],
            "model": ["m1"],
            "prompt_id": ["p1"],
            "line_count": [0]
        }
        snippets_df = pd.DataFrame(snippets_data)
        
        findings_data = {
            "snippet_id": ["s1"],
            "severity": ["HIGH"]
        }
        findings_df = pd.DataFrame(findings_data)
        
        severity_map = {"HIGH": 4}
        
        import metrics
        original_load = metrics.load_severity_map
        def mock_load(path):
            return severity_map
        metrics.load_severity_map = mock_load
        
        try:
            result = calculate_vuln_density(findings_df, snippets_df)
            s1_row = result[result["snippet_id"] == "s1"].iloc[0]
            # Should handle division by zero gracefully (set to 0.0 as per implementation)
            assert s1_row["v_per_100loc"] == 0.0
            assert s1_row["mean_severity"] == 4.0
        finally:
            metrics.load_severity_map = original_load

class TestMapSeverityToOrdinal:
    def test_known_mapping(self):
        severity_map = {"HIGH": 4, "MEDIUM": 3}
        assert map_severity_to_ordinal("HIGH", severity_map) == 4
        assert map_severity_to_ordinal("MEDIUM", severity_map) == 3
        assert map_severity_to_ordinal("low", severity_map) is None # Not in map, no fallback in this specific test context unless fallback logic is triggered
    
    def test_fallback_mapping(self):
        # Test fallback logic for common strings not in the passed map
        severity_map = {} # Empty map to force fallback
        assert map_severity_to_ordinal("HIGH", severity_map) == 4
        assert map_severity_to_ordinal("ERROR", severity_map) == 5
        assert map_severity_to_ordinal("INFO", severity_map) == 1
        assert map_severity_to_ordinal("UNKNOWN", severity_map) is None

class TestMainIntegration:
    def test_main_runs_and_creates_file(self):
        # This is a more integration-style test for the main function
        # It requires creating temp files and mocking config
        import config
        import shutil
        
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create necessary subdirectories
            data_findings = tmp_path / "data" / "findings"
            data_generated = tmp_path / "data" / "generated"
            data_results = tmp_path / "data" / "results"
            data_mappings = tmp_path / "data" / "mappings"
            
            data_findings.mkdir(parents=True)
            data_generated.mkdir(parents=True)
            data_results.mkdir(parents=True)
            data_mappings.mkdir(parents=True)
            
            # Create mock snippets.csv
            snippets_df = pd.DataFrame({
                "snippet_id": ["s1"],
                "model": ["m1"],
                "prompt_id": ["p1"],
                "line_count": [100]
            })
            snippets_df.to_csv(data_generated / "snippets.csv", index=False)
            
            # Create mock raw_findings.csv
            findings_df = pd.DataFrame({
                "snippet_id": ["s1"],
                "severity": ["HIGH"]
            })
            findings_df.to_csv(data_findings / "raw_findings.csv", index=False)
            
            # Create mock nist_severity_map.yaml
            severity_map_content = "HIGH: 4\nMEDIUM: 3\nLOW: 2"
            with open(data_mappings / "nist_severity_map.yaml", "w") as f:
                f.write(severity_map_content)
            
            # Mock config.PROJECT_ROOT and config.PATHS
            original_root = config.PROJECT_ROOT
            original_paths = config.PATHS
            
            config.PROJECT_ROOT = str(tmp_path)
            config.PATHS = {
                "SEVERITY_MAP": str(data_mappings / "nist_severity_map.yaml")
            }
            
            try:
                from metrics import main
                main()
                
                # Check if output file exists
                output_file = data_results / "raw_metrics.csv"
                assert output_file.exists()
                
                # Check content
                result_df = pd.read_csv(output_file)
                assert len(result_df) == 1
                assert result_df.iloc[0]["vuln_count"] == 1
                assert result_df.iloc[0]["v_per_100loc"] == 1.0
                
            finally:
                config.PROJECT_ROOT = original_root
                config.PATHS = original_paths