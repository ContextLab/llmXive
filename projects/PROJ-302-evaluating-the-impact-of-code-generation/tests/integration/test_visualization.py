"""
Integration test for visualization generation (T028).

This test verifies that the visualization module can:
1. Load real processed data from previous pipeline stages
2. Generate the required box plots and CDF curves
3. Save outputs to the correct paths in the figures/ directory
4. Handle edge cases (empty data, missing columns) gracefully

Prerequisites:
- T017b must have generated data/processed/diagnostic_scores.parquet
- T025 must have generated data/processed/matching_results.parquet (or similar)
- T029/T030 must have generated data/processed/sensitivity_summary.json

If any prerequisite data is missing, this test will fail loudly with a clear error.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, ensure_directories
from analysis.visualization import generate_box_plot, generate_cdf_plot, create_visualization_report, main


class TestVisualizationIntegration:
    """Integration tests for visualization generation."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and clean up after."""
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp(prefix="viz_test_")
        
        # Mock config to use test directory
        self.original_config = get_config()
        test_config = self.original_config.copy()
        test_config['paths']['figures'] = self.test_output_dir
        test_config['paths']['data_processed'] = str(project_root / "data" / "processed")
        
        # Save original and set test config
        import utils.config as config_module
        config_module._config = test_config
        
        yield
        
        # Cleanup
        shutil.rmtree(self.test_output_dir, ignore_errors=True)
        # Restore original config
        config_module._config = self.original_config
    
    def test_prerequisite_data_exists(self):
        """Verify that prerequisite data files exist before running visualization tests."""
        processed_dir = project_root / "data" / "processed"
        
        # Check for required data files
        required_files = [
            "diagnostic_scores.parquet",
            "matching_results.parquet",
            "sensitivity_summary.json"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = processed_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            pytest.fail(
                f"Prerequisite data files missing: {missing_files}. "
                f"Please run T017b, T025, and T030 first."
            )
    
    def test_load_and_validate_data(self):
        """Test that we can load and validate the required data for visualization."""
        processed_dir = project_root / "data" / "processed"
        
        # Load diagnostic scores
        try:
            diagnostic_df = pd.read_parquet(processed_dir / "diagnostic_scores.parquet")
            assert len(diagnostic_df) > 0, "Diagnostic scores dataset is empty"
            assert "snippet_id" in diagnostic_df.columns, "Missing snippet_id column"
            assert "semantic_similarity_score" in diagnostic_df.columns, "Missing semantic_similarity_score"
            assert "author_type" in diagnostic_df.columns, "Missing author_type column"
        except Exception as e:
            pytest.fail(f"Failed to load diagnostic_scores.parquet: {e}")
        
        # Load matching results
        try:
            matching_df = pd.read_parquet(processed_dir / "matching_results.parquet")
            assert len(matching_df) > 0, "Matching results dataset is empty"
            assert "review_duration" in matching_df.columns, "Missing review_duration column"
            assert "author_type" in matching_df.columns, "Missing author_type column"
            assert "matched_pair_id" in matching_df.columns, "Missing matched_pair_id column"
        except Exception as e:
            pytest.fail(f"Failed to load matching_results.parquet: {e}")
        
        # Load sensitivity summary
        try:
            import json
            with open(processed_dir / "sensitivity_summary.json", 'r') as f:
                sensitivity_data = json.load(f)
            assert "consistent" in sensitivity_data, "Missing 'consistent' flag in sensitivity summary"
            assert "stratification_results" in sensitivity_data, "Missing stratification results"
        except Exception as e:
            pytest.fail(f"Failed to load sensitivity_summary.json: {e}")
    
    def test_generate_box_plot(self):
        """Test box plot generation for review duration comparison."""
        processed_dir = project_root / "data" / "processed"
        
        # Load data
        matching_df = pd.read_parquet(processed_dir / "matching_results.parquet")
        
        # Generate box plot
        output_path = Path(self.test_output_dir) / "review_duration_boxplot.png"
        
        try:
            generate_box_plot(
                data=matching_df,
                x_col="author_type",
                y_col="review_duration",
                output_path=str(output_path),
                title="Review Duration by Code Author Type (Matched Pairs)"
            )
            
            # Verify output file exists and is not empty
            assert output_path.exists(), f"Box plot not generated at {output_path}"
            assert output_path.stat().st_size > 0, f"Box plot file is empty at {output_path}"
            
            # Verify it's a valid image (basic check)
            from PIL import Image
            img = Image.open(output_path)
            img.verify()
            
        except Exception as e:
            pytest.fail(f"Box plot generation failed: {e}")
    
    def test_generate_cdf_plot(self):
        """Test CDF plot generation for review duration distributions."""
        processed_dir = project_root / "data" / "processed"
        
        # Load data
        matching_df = pd.read_parquet(processed_dir / "matching_results.parquet")
        
        # Generate CDF plot
        output_path = Path(self.test_output_dir) / "review_duration_cdf.png"
        
        try:
            generate_cdf_plot(
                data=matching_df,
                x_col="review_duration",
                hue_col="author_type",
                output_path=str(output_path),
                title="Cumulative Distribution of Review Duration by Author Type"
            )
            
            # Verify output file exists and is not empty
            assert output_path.exists(), f"CDF plot not generated at {output_path}"
            assert output_path.stat().st_size > 0, f"CDF plot file is empty at {output_path}"
            
            # Verify it's a valid image
            from PIL import Image
            img = Image.open(output_path)
            img.verify()
            
        except Exception as e:
            pytest.fail(f"CDF plot generation failed: {e}")
    
    def test_create_visualization_report(self):
        """Test full visualization report generation."""
        processed_dir = project_root / "data" / "processed"
        figures_dir = Path(self.test_output_dir)
        
        # Load all required data
        matching_df = pd.read_parquet(processed_dir / "matching_results.parquet")
        diagnostic_df = pd.read_parquet(processed_dir / "diagnostic_scores.parquet")
        
        with open(processed_dir / "sensitivity_summary.json", 'r') as f:
            import json
            sensitivity_data = json.load(f)
        
        # Generate full report
        try:
            report_path = create_visualization_report(
                matching_data=matching_df,
                diagnostic_data=diagnostic_df,
                sensitivity_data=sensitivity_data,
                output_dir=str(figures_dir),
                base_name="integration_test_report"
            )
            
            # Verify report file exists
            assert Path(report_path).exists(), f"Visualization report not generated at {report_path}"
            assert Path(report_path).stat().st_size > 0, f"Visualization report is empty"
            
            # Verify individual plots were created
            expected_plots = [
                figures_dir / "review_duration_boxplot.png",
                figures_dir / "review_duration_cdf.png",
                figures_dir / "sensitivity_stratification.png"
            ]
            
            for plot_path in expected_plots:
                assert plot_path.exists(), f"Expected plot missing: {plot_path}"
                assert plot_path.stat().st_size > 0, f"Plot file is empty: {plot_path}"
                
        except Exception as e:
            pytest.fail(f"Visualization report generation failed: {e}")
    
    def test_empty_data_handling(self):
        """Test that visualization functions handle empty data gracefully."""
        empty_df = pd.DataFrame(columns=["author_type", "review_duration"])
        output_path = Path(self.test_output_dir) / "empty_test.png"
        
        # Should raise a clear error, not crash silently
        with pytest.raises(ValueError, match=".*empty.*dataset.*"):
            generate_box_plot(
                data=empty_df,
                x_col="author_type",
                y_col="review_duration",
                output_path=str(output_path)
            )
    
    def test_missing_column_handling(self):
        """Test that visualization functions handle missing columns gracefully."""
        incomplete_df = pd.DataFrame({"author_type": ["human", "llm"]})
        output_path = Path(self.test_output_dir) / "missing_col_test.png"
        
        # Should raise a clear error for missing required column
        with pytest.raises(KeyError, match=".*review_duration.*"):
            generate_box_plot(
                data=incomplete_df,
                x_col="author_type",
                y_col="review_duration",
                output_path=str(output_path)
            )
    
    def test_main_entry_point(self):
        """Test the main entry point of the visualization module."""
        # This test ensures the main() function can be called without errors
        # when prerequisite data exists
        
        # Temporarily modify sys.argv to simulate command-line execution
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["test_visualization.py"]  # No arguments, use defaults
            
            # This should run without errors if all prerequisites are met
            # Note: main() may print output but shouldn't raise exceptions
            main()
            
        except Exception as e:
            # If main() fails, it should be due to missing data or configuration,
            # not code errors
            pytest.fail(f"main() entry point failed: {e}")
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
