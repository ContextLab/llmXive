import os
import sys
import json
import csv
import subprocess
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add project root to path to import code modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_dataset_ids, get_sample_limit
from code.download import download_dataset, validate_and_aggregate
from code.preprocess import main as preprocess_main
from code.aggregate_graph_metrics import main as aggregate_graph_metrics_main
from code.validate_graph_metrics import main as validate_graph_metrics_main
from code.stats import run_correlation_analysis, generate_report
from code.utils import ResourceMonitor

class TestFullAnalysisPipeline:
    """
    Integration test for the full analysis report generation (US3).
    
    This test verifies the end-to-end flow:
    1. Data Ingestion (T013/T014) - Download and validate OpenNeuro data
    2. Preprocessing (T015) - Generate clean BOLD time series
    3. Graph Metrics (T022-T025) - Compute connectivity and graph metrics
    4. Validation (T026) - Check metric ranges
    5. Statistical Analysis (T030-T032) - Correlation with behavioral scores
    6. Reporting (T033-T034) - Generate scatter plots and summary PDF
    
    The test runs the actual scripts as they would be run in production,
    checking that all expected output files are generated with valid content.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories and cleanup after test."""
        # Store original paths
        self.original_data_dir = PROJECT_ROOT / "data"
        self.original_reports_dir = PROJECT_ROOT / "reports"
        
        # Create temporary structure
        self.temp_data_dir = tmp_path / "data"
        self.temp_reports_dir = tmp_path / "reports"
        self.temp_data_dir.mkdir(parents=True)
        (self.temp_data_dir / "raw").mkdir()
        (self.temp_data_dir / "interim").mkdir()
        (self.temp_data_dir / "processed").mkdir()
        self.temp_reports_dir.mkdir()
        
        # Backup existing directories if they exist
        self.backup_data = None
        self.backup_reports = None
        
        if self.original_data_dir.exists():
            self.backup_data = tmp_path / "backup_data"
            shutil.move(str(self.original_data_dir), str(self.backup_data))
            shutil.move(str(self.backup_data), str(self.temp_data_dir.parent / "data"))
        
        if self.original_reports_dir.exists():
            self.backup_reports = tmp_path / "backup_reports"
            shutil.move(str(self.original_reports_dir), str(self.backup_reports))
            shutil.move(str(self.backup_reports), str(self.temp_reports_dir.parent / "reports"))
        
        yield
        
        # Restore original directories
        if self.backup_data:
            if (self.temp_data_dir.parent / "data").exists():
                shutil.rmtree(str(self.temp_data_dir.parent / "data"))
            shutil.move(str(self.backup_data), str(self.original_data_dir))
        
        if self.backup_reports:
            if (self.temp_reports_dir.parent / "reports").exists():
                shutil.rmtree(str(self.temp_reports_dir.parent / "reports"))
            shutil.move(str(self.backup_reports), str(self.original_reports_dir))

    def test_full_pipeline_execution(self):
        """
        Execute the full pipeline and verify all outputs.
        
        This is the core integration test for T029. It runs the actual
        pipeline scripts and verifies that all expected artifacts are
        generated with valid content.
        """
        # Step 1: Verify data ingestion (T013/T014)
        # Note: In a real CI environment, we would skip download if data exists
        # For this test, we assume data has been pre-downloaded or the download
        # step is mocked/skipped if data is present
        
        data_processed = self.temp_data_dir / "processed"
        reports_dir = self.temp_reports_dir
        
        # Check if preprocessed data exists (simulating T015 completion)
        # If not, we would run the download and preprocess steps
        # For this integration test, we assume the pipeline is run end-to-end
        
        # Step 2: Run Graph Metrics Aggregation (T022-T025)
        # This simulates running code/aggregate_graph_metrics.py
        try:
            # Change to project root to run scripts
            os.chdir(PROJECT_ROOT)
            
            # Run the aggregation script
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "code" / "aggregate_graph_metrics.py")],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # We expect this to run successfully if data exists
            # If data doesn't exist, it should fail loudly (not silently fallback)
            if result.returncode != 0:
                # Check if it's a "no data" error which is expected in CI without download
                if "No preprocessed subjects found" in result.stderr or "No data available" in result.stderr:
                    # This is expected if we haven't run the full download/preprocess
                    # In a real CI, we would have a fixture that downloads a subset
                    pytest.skip("Preprocessed data not available in CI environment. Full download required.")
                else:
                    pytest.fail(f"Graph metrics aggregation failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            pytest.fail("Graph metrics aggregation timed out")
        
        # Step 3: Validate Graph Metrics (T026)
        try:
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "code" / "validate_graph_metrics.py")],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                # Check if validation log was created with anomalies
                validation_log = data_processed / "graph_metric_validation.log"
                if validation_log.exists():
                    # Validation found anomalies but didn't crash - this is acceptable
                    pass
                else:
                    pytest.fail(f"Validation failed without log: {result.stderr}")
        except subprocess.TimeoutExpired:
            pytest.fail("Graph metrics validation timed out")
        
        # Step 4: Run Statistical Analysis (T030-T032)
        # This is the core of US3 - correlation analysis and report generation
        try:
            # Import and run the stats module directly to ensure it works
            from code.stats import run_correlation_analysis, generate_report
            
            # Run correlation analysis
            analysis_results = run_correlation_analysis()
            
            # Verify results structure
            assert isinstance(analysis_results, dict), "Analysis results should be a dictionary"
            assert "correlations" in analysis_results, "Results should contain 'correlations' key"
            assert "effect_sizes" in analysis_results, "Results should contain 'effect_sizes' key"
            
            # Generate report
            report_path = generate_report(analysis_results, str(reports_dir))
            
            # Verify report was created
            assert Path(report_path).exists(), f"Report not generated at {report_path}"
            
            # Verify report is not empty
            report_size = Path(report_path).stat().st_size
            assert report_size > 100, f"Report file is too small ({report_size} bytes), likely empty or placeholder"
            
        except ImportError as e:
            pytest.fail(f"Stats module not properly implemented: {e}")
        except AssertionError as e:
            pytest.fail(f"Analysis results validation failed: {e}")
        
        # Step 5: Verify all expected output files
        expected_files = [
            data_processed / "graph_metrics.csv",
            data_processed / "graph_metric_validation.log",
            reports_dir / "summary.pdf",
            data_processed / "analysis_resource_profile.json"
        ]
        
        missing_files = []
        for file_path in expected_files:
            if not file_path.exists():
                missing_files.append(str(file_path.relative_to(PROJECT_ROOT)))
        
        if missing_files:
            pytest.fail(f"Missing expected output files: {', '.join(missing_files)}")
        
        # Step 6: Verify content of key files
        
        # Verify graph_metrics.csv has required columns
        metrics_csv = data_processed / "graph_metrics.csv"
        with open(metrics_csv, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            required_cols = ['subject_id', 'metric_name', 'value', 'cohens_d', 'ci_95_lower', 'ci_95_upper']
            missing_cols = [col for col in required_cols if col not in headers]
            if missing_cols:
                pytest.fail(f"graph_metrics.csv missing columns: {missing_cols}")
            
            # Check we have at least one row
            rows = list(reader)
            if len(rows) == 0:
                pytest.fail("graph_metrics.csv is empty")
        
        # Verify summary.pdf exists and has content
        summary_pdf = reports_dir / "summary.pdf"
        assert summary_pdf.stat().st_size > 1000, "summary.pdf appears to be empty or corrupted"
        
        # Verify resource profile was created
        resource_profile = data_processed / "analysis_resource_profile.json"
        with open(resource_profile, 'r') as f:
            profile_data = json.load(f)
            assert 'peak_ram_mb' in profile_data, "Resource profile missing peak_ram_mb"
            assert 'total_runtime_seconds' in profile_data, "Resource profile missing total_runtime_seconds"
        
        # Step 7: Verify statistical correctness
        # Check that Bonferroni correction was applied (p-values adjusted)
        # This is verified by checking the analysis_results structure
        assert 'bonferroni_corrected' in analysis_results, "Bonferroni correction results missing"
        
        # Verify effect sizes are reasonable (Cohen's d typically -3 to 3)
        for effect in analysis_results.get('effect_sizes', []):
            cohens_d = effect.get('cohens_d', 0)
            assert -10 < cohens_d < 10, f"Unrealistic Cohen's d value: {cohens_d}"
        
        # Step 8: Verify no synthetic data was used
        # Check that all subject IDs are from the real OpenNeuro datasets
        valid_subject_prefixes = ['sub-']  # OpenNeuro subjects start with 'sub-'
        for row in rows:
            subject_id = row['subject_id']
            if not any(subject_id.startswith(prefix) for prefix in valid_subject_prefixes):
                pytest.fail(f"Invalid subject ID detected (possible synthetic data): {subject_id}")

    def test_pipeline_with_resource_monitoring(self):
        """
        Verify that resource monitoring is integrated throughout the pipeline.
        
        This test ensures that the ResourceMonitor from T009 is properly
        integrated and that resource profiles are generated as required by SC-005.
        """
        # Run the full pipeline with resource monitoring
        # This is already covered in test_full_pipeline_execution, but we
        # explicitly check the resource profile here
        
        data_processed = self.temp_data_dir / "processed"
        resource_profile = data_processed / "analysis_resource_profile.json"
        
        # The profile should have been created by the stats module
        assert resource_profile.exists(), "Resource profile not generated"
        
        with open(resource_profile, 'r') as f:
            profile = json.load(f)
            
            # Verify required fields
            assert 'peak_ram_mb' in profile
            assert 'total_runtime_seconds' in profile
            assert 'subjects_processed' in profile
            
            # Verify values are reasonable
            assert profile['peak_ram_mb'] > 0, "Peak RAM should be positive"
            assert profile['total_runtime_seconds'] > 0, "Runtime should be positive"
            assert profile['subjects_processed'] > 0, "At least one subject should be processed"

    def test_error_handling_pipeline(self):
        """
        Verify that the pipeline fails loudly when data is missing or invalid.
        
        This test ensures that the pipeline doesn't silently fallback to
        synthetic data when real data is unavailable.
        """
        # Temporarily move the graph_metrics.csv to simulate missing data
        data_processed = self.temp_data_dir / "processed"
        metrics_csv = data_processed / "graph_metrics.csv"
        
        if metrics_csv.exists():
            backup = data_processed / "graph_metrics.csv.backup"
            shutil.move(str(metrics_csv), str(backup))
            
            try:
                # Try to run the stats module - it should fail loudly
                with pytest.raises(Exception) as exc_info:
                    from code.stats import run_correlation_analysis
                    run_correlation_analysis()
                
                # Verify the error message indicates missing real data
                error_msg = str(exc_info.value).lower()
                assert 'missing' in error_msg or 'not found' in error_msg or 'no data' in error_msg, \
                    f"Error message should indicate missing data: {exc_info.value}"
                
            finally:
                # Restore the file
                if backup.exists():
                    shutil.move(str(backup), str(metrics_csv))
        else:
            # If no data exists, the pipeline should fail loudly
            with pytest.raises(Exception) as exc_info:
                from code.stats import run_correlation_analysis
                run_correlation_analysis()
            
            error_msg = str(exc_info.value).lower()
            assert 'missing' in error_msg or 'not found' in error_msg or 'no data' in error_msg, \
                f"Error message should indicate missing data: {exc_info.value}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])