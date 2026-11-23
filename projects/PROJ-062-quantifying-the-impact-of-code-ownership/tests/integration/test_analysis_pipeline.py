"""
Integration tests for the full statistical analysis pipeline (User Story 3).

This test verifies that the full statistical output JSON and plot generation
work correctly end-to-end, assuming that data from US1 and US2 is available.
"""
import os
import sys
import json
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_output_dir, get_repo_list
from code.metrics_calc import process_all_ownership_for_size_age, save_size_age_metrics
from code.statistical_analysis import (
    load_metric_data,
    calculate_spearman_correlation,
    calculate_correlation_confidence_interval,
    calculate_vif,
    test_non_linearity,
    apply_multiple_comparison_correction,
    perform_sensitivity_analysis_pvalue,
    perform_sensitivity_analysis_rho,
    run_full_analysis,
    main as statistical_main
)
from code.visualizations import generate_all_plots, main as viz_main
from code.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestAnalysisPipelineIntegration:
    """Integration tests for the statistical analysis and visualization pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and clean up after tests."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_analysis_"))
        self.original_output_dir = os.environ.get("OUTPUT_DIR")
        
        # Set up test output directory
        os.environ["OUTPUT_DIR"] = str(self.test_dir)
        
        # Create necessary subdirectories
        (self.test_dir / "data" / "results").mkdir(parents=True, exist_ok=True)
        (self.test_dir / "figures").mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Cleanup
        if self.original_output_dir:
            os.environ["OUTPUT_DIR"] = self.original_output_dir
        else:
            os.environ.pop("OUTPUT_DIR", None)
        
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mock_metric_data(self, data_dir: Path):
        """Create mock metric data files that simulate US2 output."""
        # Create metrics CSV with Gini, Size, Age, Bug Density
        metrics_csv = data_dir / "aggregated_metrics.csv"
        with open(metrics_csv, "w", newline="") as f:
            writer = f.write
            writer("repo,module,gini,size_kloc,age_months,bug_density\n")
            # Write realistic mock data
            writer("repo1,module_a,0.65,12.5,24,0.8\n")
            writer("repo1,module_b,0.45,8.2,18,0.3\n")
            writer("repo1,module_c,0.82,45.1,36,1.5\n")
            writer("repo2,module_x,0.33,5.7,12,0.1\n")
            writer("repo2,module_y,0.71,22.3,28,0.9\n")
            writer("repo3,module_p,0.55,15.8,20,0.4\n")
            writer("repo3,module_q,0.28,3.2,8,0.05\n")
            writer("repo3,module_r,0.91,67.4,48,2.1\n")
        
        # Create size/age CSV
        size_age_csv = data_dir / "size_age_metrics.csv"
        with open(size_age_csv, "w", newline="") as f:
            writer = f.write
            writer("repo,module,size_kloc,age_months\n")
            writer("repo1,module_a,12.5,24\n")
            writer("repo1,module_b,8.2,18\n")
            writer("repo1,module_c,45.1,36\n")
            writer("repo2,module_x,5.7,12\n")
            writer("repo2,module_y,22.3,28\n")
            writer("repo3,module_p,15.8,20\n")
            writer("repo3,module_q,3.2,8\n")
            writer("repo3,module_r,67.4,48\n")

    def test_run_full_analysis(self):
        """Test that run_full_analysis produces valid JSON output."""
        data_dir = self.test_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock data
        self._create_mock_metric_data(data_dir)
        
        # Run full analysis
        output_file = data_dir / "results" / "full_analysis_results.json"
        
        result = run_full_analysis(
            metrics_path=str(data_dir / "aggregated_metrics.csv"),
            output_path=str(output_file)
        )
        
        # Verify output file exists
        assert output_file.exists(), "Full analysis output file was not created"
        
        # Verify JSON structure
        with open(output_file, "r") as f:
            analysis_output = json.load(f)
        
        # Check required keys
        assert "correlations" in analysis_output, "Missing correlations section"
        assert "vif_analysis" in analysis_output, "Missing VIF analysis section"
        assert "non_linearity_test" in analysis_output, "Missing non-linearity test section"
        assert "sensitivity_analysis" in analysis_output, "Missing sensitivity analysis section"
        
        # Verify correlation results
        correlations = analysis_output["correlations"]
        assert "gini_bug_density" in correlations, "Missing Gini vs bug density correlation"
        assert "rho" in correlations["gini_bug_density"], "Missing correlation coefficient"
        assert "p_value" in correlations["gini_bug_density"], "Missing p-value"
        assert "ci_lower" in correlations["gini_bug_density"], "Missing CI lower bound"
        assert "ci_upper" in correlations["gini_bug_density"], "Missing CI upper bound"
        
        # Verify VIF results
        vif_results = analysis_output["vif_analysis"]
        assert "gini" in vif_results, "Missing Gini VIF"
        assert "gini_squared" in vif_results, "Missing Gini² VIF"
        assert "size" in vif_results, "Missing Size VIF"
        assert "age" in analysis_output["vif_analysis"], "Missing Age VIF"
        
        # Verify non-linearity test
        non_linear = analysis_output["non_linearity_test"]
        assert "quadratic_p_value" in non_linear, "Missing quadratic term p-value"
        assert "lrt_p_value" in non_linear, "Missing LRT p-value"
        
        # Verify sensitivity analysis
        sensitivity = analysis_output["sensitivity_analysis"]
        assert "pvalue_sweep" in sensitivity, "Missing p-value sensitivity sweep"
        assert "rho_sweep" in sensitivity, "Missing rho sensitivity sweep"
        
        # Verify data integrity
        assert correlations["gini_bug_density"]["rho"] > -1.0 and \
               correlations["gini_bug_density"]["rho"] <= 1.0, \
               "Correlation coefficient out of bounds"
        
        logger.info("Full analysis JSON structure validated successfully")

    def test_plot_generation(self):
        """Test that scatter plots are generated correctly."""
        data_dir = self.test_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        figures_dir = self.test_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock data
        self._create_mock_metric_data(data_dir)
        
        # Generate plots
        output_dir = str(figures_dir)
        metrics_path = str(data_dir / "aggregated_metrics.csv")
        
        plot_results = generate_all_plots(
            metrics_path=metrics_path,
            output_dir=output_dir
        )
        
        # Verify plots were created
        assert "plots_created" in plot_results, "Plot generation did not return results"
        assert plot_results["plots_created"] > 0, "No plots were created"
        
        # Verify plot files exist
        plot_files = list(figures_dir.glob("*.png"))
        assert len(plot_files) > 0, "No PNG files were created in figures directory"
        
        # Verify at least one plot has the expected naming convention
        expected_plot_name = "gini_vs_bug_density_scatter.png"
        found_expected = False
        for plot_file in plot_files:
            if "gini" in plot_file.name.lower() and "scatter" in plot_file.name.lower():
                found_expected = True
                # Verify file is not empty and has reasonable size
                assert plot_file.stat().st_size > 1000, \
                    f"Plot file {plot_file.name} appears to be too small or empty"
                break
        
        assert found_expected, "Expected Gini vs Bug Density scatter plot was not found"
        
        logger.info(f"Generated {len(plot_files)} plot files successfully")

    def test_end_to_end_pipeline(self):
        """Test the complete end-to-end statistical analysis pipeline."""
        data_dir = self.test_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        results_dir = data_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        figures_dir = self.test_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock data
        self._create_mock_metric_data(data_dir)
        
        # Run the complete pipeline
        # This simulates what main.py would do for US3
        metrics_path = str(data_dir / "aggregated_metrics.csv")
        
        # 1. Run statistical analysis
        analysis_output = run_full_analysis(
            metrics_path=metrics_path,
            output_path=str(results_dir / "full_analysis_results.json")
        )
        
        assert analysis_output["status"] == "success", \
            f"Statistical analysis failed: {analysis_output.get('error', 'Unknown error')}"
        
        # 2. Generate visualizations
        plot_results = generate_all_plots(
            metrics_path=metrics_path,
            output_dir=str(figures_dir)
        )
        
        assert plot_results["plots_created"] > 0, \
            "Visualization generation failed to create plots"
        
        # 3. Verify final report structure
        final_report_path = results_dir / "final_report.json"
        
        # Create a minimal final report that would be generated by main.py
        final_report = {
            "analysis_status": "complete",
            "correlations": analysis_output["correlations"],
            "vif_analysis": analysis_output["vif_analysis"],
            "non_linearity_test": analysis_output["non_linearity_test"],
            "sensitivity_analysis": analysis_output["sensitivity_analysis"],
            "plots_generated": plot_results["plots_created"],
            "metadata": {
                "pipeline_version": "1.0",
                "analysis_type": "associational",
                "repos_processed": 3,
                "modules_analyzed": 8
            }
        }
        
        with open(final_report_path, "w") as f:
            json.dump(final_report, f, indent=2)
        
        # Verify final report
        assert final_report_path.exists(), "Final report was not created"
        
        with open(final_report_path, "r") as f:
            report = json.load(f)
        
        assert report["analysis_status"] == "complete", "Analysis status not complete"
        assert report["metadata"]["analysis_type"] == "associational", \
            "Final report missing associational framing"
        
        # Verify all required sections are present
        required_sections = [
            "correlations", "vif_analysis", "non_linearity_test", 
            "sensitivity_analysis", "plots_generated"
        ]
        
        for section in required_sections:
            assert section in report, f"Missing required section: {section}"
        
        logger.info("End-to-end pipeline completed successfully")

    def test_sensitivity_analysis_outputs(self):
        """Test that sensitivity analysis produces correct CSV outputs."""
        data_dir = self.test_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        results_dir = data_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock data
        self._create_mock_metric_data(data_dir)
        
        # Run sensitivity analyses
        pvalue_results = perform_sensitivity_analysis_pvalue(
            metrics_path=str(data_dir / "aggregated_metrics.csv"),
            output_path=str(results_dir / "sensitivity_pvalue.csv")
        )
        
        rho_results = perform_sensitivity_analysis_rho(
            metrics_path=str(data_dir / "aggregated_metrics.csv"),
            output_path=str(results_dir / "sensitivity_rho.csv")
        )
        
        # Verify CSV files exist
        pvalue_csv = results_dir / "sensitivity_pvalue.csv"
        rho_csv = results_dir / "sensitivity_rho.csv"
        
        assert pvalue_csv.exists(), "P-value sensitivity CSV not created"
        assert rho_csv.exists(), "Rho sensitivity CSV not created"
        
        # Verify CSV structure
        with open(pvalue_csv, "r") as f:
            pvalue_content = f.read()
            assert "cutoff" in pvalue_content, "Missing cutoff column in p-value CSV"
            assert "count_significant" in pvalue_content, "Missing count_significant column"
            assert "count_total" in pvalue_content, "Missing count_total column"
            
            # Verify expected cutoffs are present
            assert "0.01" in pvalue_content, "Missing 0.01 cutoff"
            assert "0.05" in pvalue_content, "Missing 0.05 cutoff"
            assert "0.1" in pvalue_content, "Missing 0.1 cutoff"
        
        with open(rho_csv, "r") as f:
            rho_content = f.read()
            assert "cutoff" in rho_content, "Missing cutoff column in rho CSV"
            assert "count_significant" in rho_content, "Missing count_significant column"
            assert "count_total" in rho_content, "Missing count_total column"
            
            # Verify expected cutoffs are present
            assert "0.2" in rho_content, "Missing 0.2 cutoff"
            assert "0.3" in rho_content, "Missing 0.3 cutoff"
            assert "0.4" in rho_content, "Missing 0.4 cutoff"
        
        logger.info("Sensitivity analysis CSV outputs validated")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])