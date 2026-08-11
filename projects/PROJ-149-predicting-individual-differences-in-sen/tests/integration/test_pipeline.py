"""
Integration test for the end-to-end EEG Sensory Speed Prediction pipeline.

This test verifies the full flow from data download to final report generation,
ensuring all components work together correctly.

Prerequisites:
- T007: Data downloaded (data/raw/)
- T008a: Feasibility check passed (data/interim/joined_metadata.csv)
- T010-T032: All preprocessing, feature extraction, modeling, and reporting scripts
  have executed successfully.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_path, ensure_dirs


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_001_data_download_complete(self, project_root):
        """Verify that raw data has been downloaded."""
        data_raw = project_root / "data" / "raw"
        assert data_raw.exists(), "Raw data directory missing"
        
        # Check for expected PhysioNet files
        eeg_files = list(data_raw.glob("*EEG*.tar.gz"))
        behavioral_files = list(data_raw.glob("*behavioral*"))
        
        assert len(eeg_files) > 0, "No EEG data files found"
        assert len(behavioral_files) > 0, "No behavioral data files found"
    
    def test_002_feasibility_check_passed(self, project_root):
        """Verify that feasibility check completed successfully."""
        joined_metadata = project_root / "data" / "interim" / "joined_metadata.csv"
        feasibility_report = project_root / "data" / "processed" / "feasibility_report.md"
        
        # Either joined_metadata exists (success) or feasibility_report exists (failure)
        # For a successful pipeline, joined_metadata should exist
        assert joined_metadata.exists(), "Joined metadata file missing - feasibility check may have failed"
        
        # Check that the file is not empty
        assert joined_metadata.stat().st_size > 0, "Joined metadata file is empty"
    
    def test_003_preprocessing_complete(self, project_root):
        """Verify that EEG preprocessing completed."""
        cleaned_eeg_dir = project_root / "data" / "interim" / "cleaned_eeg"
        assert cleaned_eeg_dir.exists(), "Cleaned EEG directory missing"
        
        # Check for cleaned data files
        cleaned_files = list(cleaned_eeg_dir.glob("*.fif"))
        assert len(cleaned_files) > 0, "No cleaned EEG files found"
    
    def test_004_feature_extraction_complete(self, project_root):
        """Verify that feature extraction completed."""
        eeg_psd = project_root / "data" / "interim" / "eeg_psd.csv"
        behavioral_metrics = project_root / "data" / "interim" / "behavioral_metrics.csv"
        
        assert eeg_psd.exists(), "EEG PSD features file missing"
        assert behavioral_metrics.exists(), "Behavioral metrics file missing"
        
        assert eeg_psd.stat().st_size > 0, "EEG PSD file is empty"
        assert behavioral_metrics.stat().st_size > 0, "Behavioral metrics file is empty"
    
    def test_005_features_finalized(self, project_root):
        """Verify that final features file is ready."""
        features_file = project_root / "data" / "processed" / "features.csv"
        assert features_file.exists(), "Final features file missing"
        assert features_file.stat().st_size > 0, "Features file is empty"
    
    def test_006_modeling_complete(self, project_root):
        """Verify that modeling completed."""
        split_indices = project_root / "data" / "interim" / "split_indices.json"
        model_results = project_root / "data" / "processed" / "model_results.json"
        
        assert split_indices.exists(), "Split indices file missing"
        assert model_results.exists(), "Model results file missing"
        
        # Validate JSON structure
        with open(split_indices) as f:
            splits = json.load(f)
            assert "train" in splits and "test" in splits, "Invalid split structure"
        
        with open(model_results) as f:
            results = json.load(f)
            assert "adjusted_r2" in results or "r2" in results, "Missing model metrics"
    
    def test_007_correlations_complete(self, project_root):
        """Verify that correlation analysis completed."""
        correlations_file = project_root / "data" / "processed" / "correlations.csv"
        assert correlations_file.exists(), "Correlations file missing"
        assert correlations_file.stat().st_size > 0, "Correlations file is empty"
    
    def test_008_robustness_complete(self, project_root):
        """Verify that robustness analysis completed."""
        robustness_report = project_root / "data" / "processed" / "robustness_report.csv"
        assert robustness_report.exists(), "Robustness report missing"
        assert robustness_report.stat().st_size > 0, "Robustness report is empty"
    
    def test_009_sensitivity_complete(self, project_root):
        """Verify that sensitivity analysis completed."""
        sensitivity_plot = project_root / "data" / "processed" / "sensitivity_plot.png"
        assert sensitivity_plot.exists(), "Sensitivity plot missing"
    
    def test_010_final_report_complete(self, project_root):
        """Verify that final report was generated."""
        final_report = project_root / "data" / "processed" / "final_report.md"
        assert final_report.exists(), "Final report missing"
        assert final_report.stat().st_size > 0, "Final report is empty"
    
    def test_011_success_criteria_verified(self, project_root):
        """Verify that success criteria were checked."""
        verification_log = project_root / "data" / "processed" / "verification_log.json"
        assert verification_log.exists(), "Verification log missing"
        
        with open(verification_log) as f:
            log = json.load(f)
            # Check that all success criteria were evaluated
            expected_keys = ["SC-001", "SC-002", "SC-003", "SC-004", "SC-005"]
            for key in expected_keys:
                assert key in log, f"Missing verification for {key}"
    
    def test_012_pipeline_artifacts_integrity(self, project_root):
        """Verify integrity of all key pipeline artifacts."""
        artifacts = [
            ("data/interim/joined_metadata.csv", "CSV"),
            ("data/interim/cleaned_eeg", "DIR"),
            ("data/interim/eeg_psd.csv", "CSV"),
            ("data/interim/behavioral_metrics.csv", "CSV"),
            ("data/processed/features.csv", "CSV"),
            ("data/interim/split_indices.json", "JSON"),
            ("data/processed/model_results.json", "JSON"),
            ("data/processed/correlations.csv", "CSV"),
            ("data/processed/robustness_report.csv", "CSV"),
            ("data/processed/sensitivity_plot.png", "FILE"),
            ("data/processed/final_report.md", "FILE"),
            ("data/processed/verification_log.json", "JSON"),
        ]
        
        for artifact_path, artifact_type in artifacts:
            full_path = project_root / artifact_path
            assert full_path.exists(), f"Missing artifact: {artifact_path}"
            
            if artifact_type == "CSV":
                assert full_path.stat().st_size > 0, f"Empty CSV: {artifact_path}"
            elif artifact_type == "JSON":
                assert full_path.stat().st_size > 0, f"Empty JSON: {artifact_path}"
                try:
                    with open(full_path) as f:
                        json.load(f)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON: {artifact_path}")
            elif artifact_type == "DIR":
                files = list(full_path.glob("*"))
                assert len(files) > 0, f"Empty directory: {artifact_path}"
    
    def test_013_data_flow_consistency(self, project_root):
        """Verify that data flows correctly through the pipeline."""
        import pandas as pd
        
        # Load features and check structure
        features = pd.read_csv(project_root / "data" / "processed" / "features.csv")
        assert "participant_id" in features.columns, "Missing participant_id in features"
        assert "median_rt" in features.columns, "Missing median_rt in features"
        
        # Load model results and verify it references the features
        with open(project_root / "data" / "processed" / "model_results.json") as f:
            results = json.load(f)
        
        # Check that model was trained on the correct number of participants
        n_participants = len(features)
        assert results.get("n_samples", 0) == n_participants, "Mismatch in sample count"
    
    def test_014_script_executability(self, project_root):
        """Verify that all pipeline scripts are executable and importable."""
        scripts = [
            "code/00_feasibility_check_join.py",
            "code/01_download_data.py",
            "code/02_preprocess_eeg.py",
            "code/03_extract_features.py",
            "code/04_modeling.py",
            "code/05_robustness_analysis.py",
            "code/06_sensitivity_analysis.py",
            "code/07_generate_report.py",
        ]
        
        for script_rel_path in scripts:
            script_path = project_root / script_rel_path
            assert script_path.exists(), f"Script missing: {script_rel_path}"
            
            # Try importing the script to check for syntax errors
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("temp_module", script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                pytest.fail(f"Script {script_rel_path} has import/syntax errors: {str(e)}")
    
    def test_015_final_report_content(self, project_root):
        """Verify that the final report contains expected sections."""
        report_path = project_root / "data" / "processed" / "final_report.md"
        
        with open(report_path) as f:
            report_content = f.read()
        
        # Check for key sections
        required_sections = [
            "## Executive Summary",
            "## Methodology",
            "## Results",
            "## Correlation Analysis",
            "## Model Performance",
            "## Robustness Analysis",
            "## Sensitivity Analysis",
            "## Conclusions",
        ]
        
        for section in required_sections:
            assert section in report_content, f"Missing section in report: {section}"
        
        # Check for key metrics
        assert "Adjusted R²" in report_content, "Missing Adjusted R² in report"
        assert "Bonferroni" in report_content, "Missing Bonferroni correction mention"
        assert "p-value" in report_content, "Missing p-value mention"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])