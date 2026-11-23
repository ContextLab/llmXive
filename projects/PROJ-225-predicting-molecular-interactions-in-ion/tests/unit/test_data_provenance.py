import pytest
import json
import os
import pandas as pd
from code.analysis import (
    determine_data_sources,
    write_validation_report_with_provenance,
    aggregate_validation_results
)

class TestDataProvenance:
    """Test data provenance functionality for validation report."""

    def test_determine_data_sources_default(self, tmp_path):
        """Test that default data sources are correctly identified."""
        # Create minimal directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "raw").mkdir()
        (data_dir / "validation").mkdir()
        
        # Change to temp directory to avoid affecting real paths
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            sources = determine_data_sources()
            
            assert "training_data_source" in sources
            assert "validation_data_source" in sources
            assert sources["training_data_source"] in ["SPICE", "Synthetic (IL-SAPT fallback)"]
            assert sources["validation_data_source"] in ["DFT", "Experimental"]
        finally:
            os.chdir(original_cwd)

    def test_write_validation_report_with_provenance(self, tmp_path):
        """Test that validation report includes data provenance section."""
        # Create sample validation results
        anova_results = {"f_statistic": 5.0, "p_value": 0.01}
        tukey_results = {"significant_groups": ["Group A vs Group B"]}
        dft_mae = {"electrostatic": 0.5, "dispersion": 0.3, "hbond": 0.2}
        experimental_status = "pending"
        tautology_check = {"tautology_detected": False}
        
        report = aggregate_validation_results(
            anova_results, tukey_results, dft_mae, experimental_status, tautology_check
        )
        
        data_sources = {
            "training_data_source": "SPICE",
            "validation_data_source": "DFT"
        }
        
        output_path = tmp_path / "validation_report.json"
        
        # Write report with provenance
        result = write_validation_report_with_provenance(
            report, str(output_path), data_sources
        )
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify JSON is valid and contains provenance
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert "data_provenance" in saved_report
        assert saved_report["data_provenance"]["training_data_source"] == "SPICE"
        assert saved_report["data_provenance"]["validation_data_source"] == "DFT"
        
        # Verify original report data is preserved
        assert "anova_results" in saved_report
        assert "dft_validation_mae" in saved_report

    def test_provenance_contains_required_strings(self, tmp_path):
        """Test that provenance section contains required source strings."""
        report = {}
        data_sources = {
            "training_data_source": "SPICE",
            "validation_data_source": "DFT"
        }
        
        output_path = tmp_path / "test_report.json"
        write_validation_report_with_provenance(report, str(output_path), data_sources)
        
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        provenance = saved_report["data_provenance"]
        
        # Check for required strings
        assert "SPICE" in provenance["training_data_source"] or "Synthetic" in provenance["training_data_source"]
        assert "DFT" in provenance["validation_data_source"] or "Experimental" in provenance["validation_data_source"]
