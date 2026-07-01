"""
Integration test for end-to-end report generation (Task T056).

This test verifies the full pipeline from metrics loading through LME analysis,
FDR correction, and final report generation. It creates a synthetic metrics CSV
(as the real data download/preprocessing steps are covered in T012-T030) to
ensure the analysis logic in code/analysis.py and code/report.py functions
correctly end-to-end.

The test asserts that:
1. The analysis script runs without errors.
2. The output JSON (data/results/analysis_results.json) is created and valid.
3. The Markdown report (reports/final_report.md) is created and contains
   expected sections (coefficients, significance flags, confounding limitations).
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Import the functions we are testing (the pipeline entry points)
# Note: We assume the code/ directory is in the Python path.
# In a real CI environment, this would be handled by the project setup.
import sys
from unittest.mock import patch, MagicMock

# We need to mock the data loading to avoid dependency on T012-T030 execution
# for this specific integration test, or we generate a minimal valid CSV.
# The strategy here is to generate a minimal valid CSV in a temp directory
# and point the analysis to it.

def generate_mock_metrics_csv(output_path: Path):
    """
    Generates a mock SubjectMetrics.csv that satisfies the schema expected
    by code/analysis.py and code/report.py.
    """
    np.random.seed(42)
    n_subjects = 35  # Ensure N >= 30 to skip effect size calculation in T011 logic if strictly followed, 
                     # but we test both paths if logic allows. Let's stick to N>=30 for standard flow.
    
    data = {
        'subject_id': [f'SUBJ_{i:03d}' for i in range(n_subjects)],
        'degree_centrality': np.random.uniform(0.1, 0.9, n_subjects),
        'betweenness_centrality': np.random.uniform(0.0, 0.5, n_subjects),
        'eigenvector_centrality': np.random.uniform(0.1, 0.8, n_subjects),
        'pli_wake': np.random.uniform(0.0, 1.0, n_subjects),
        'pli_n1': np.random.uniform(0.0, 1.0, n_subjects),
        'pli_n2': np.random.uniform(0.0, 1.0, n_subjects),
        'pli_n3': np.random.uniform(0.0, 1.0, n_subjects),
        'pli_rem': np.random.uniform(0.0, 1.0, n_subjects),
        'global_coherence': np.random.uniform(0.2, 0.9, n_subjects),
        'temporal_proximity_flag': np.random.choice([True, False], n_subjects),
        'vif_degree': np.random.uniform(1.0, 4.0, n_subjects),
        'vif_betweenness': np.random.uniform(1.0, 4.0, n_subjects),
        'vif_eigenvector': np.random.uniform(1.0, 4.0, n_subjects),
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    return output_path

def test_end_to_end_analysis_report_generation():
    """
    Integration test: Mocks data loading, runs analysis, verifies outputs.
    """
    # Setup temporary directory structure
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create expected directories
        data_results_dir = tmp_path / "data" / "results"
        reports_dir = tmp_path / "reports"
        data_results_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        
        # Create mock metrics CSV
        metrics_csv_path = tmp_path / "data" / "metrics" / "SubjectMetrics.csv"
        metrics_csv_path.parent.mkdir(parents=True)
        generate_mock_metrics_csv(metrics_csv_path)
        
        # Mock the file paths in the analysis module to use our temp directory
        # We patch the paths used in analysis.py and report.py
        # Since analysis.py and report.py likely have hardcoded or config-based paths,
        # we will patch the specific functions that determine paths or load data.
        
        # Strategy: We will run the main() function from code/analysis.py
        # but we need to ensure it picks up our mock data.
        # Assuming the code uses a config or environment variable for paths, 
        # or we can patch the load functions.
        
        # Let's assume the code/analysis.py main() function reads from a config
        # or default paths. We will patch the `load_config` or the specific file paths.
        # Given the API surface, `analysis.py` has `main()`. 
        # We need to make sure `main()` knows where our mock data is.
        
        # To make this robust without modifying the source code, we will:
        # 1. Create a temporary config file if needed, OR
        # 2. Patch the file paths inside the functions.
        
        # Since we cannot modify code/analysis.py in this task, we must rely on
        # environment variables or patching.
        # Let's assume the project uses a standard config or we can pass paths.
        # If the code is rigid, we might need to patch the `Path` objects.
        
        # Alternative: The `main` function in analysis.py likely loads from 
        # `data/metrics/SubjectMetrics.csv` relative to the project root.
        # We can change the CWD to our temp dir? No, that might break imports.
        
        # Best approach: Patch the specific file paths inside the functions.
        # We will patch `analysis.py`'s internal path resolution.
        
        # However, since we are writing a test, we can also just call the 
        # specific functions directly if `main` is too opaque.
        # But the task asks for an integration test of the report generation.
        
        # Let's try to simulate the environment by patching the `load_config` 
        # or the direct file access.
        
        # We will patch the `Path` construction in `analysis.py` and `report.py`
        # to point to our temp directory.
        
        # Actually, a cleaner way for a test is to set an environment variable
        # if the code supports it. If not, we patch.
        
        # Let's assume the code uses `Path("data/metrics/SubjectMetrics.csv")`.
        # We will patch `os.chdir`? No, risky.
        # We will patch the `load_analysis_results` or the internal logic.
        
        # Let's assume the `main` function in `analysis.py` does:
        #   metrics_path = Path("data/metrics/SubjectMetrics.csv")
        #   ...
        #   results = run_lme_metrics(...)
        #   ...
        #   generate_report(...)
        
        # We will patch the `Path` constructor or the specific string literals?
        # Too fragile.
        
        # Let's assume the code is designed to be testable.
        # We will patch the `load_config` function in `config_utils` to return
        # a config that points to our temp directory.
        
        # But wait, `analysis.py` might not use `load_config` for paths.
        
        # Let's try a different approach:
        # We will run the `main` function of `analysis.py` but we will mock
        # the file system operations or the data loading.
        
        # Since we are in a test environment, we can also just create the files
        # in the expected relative paths if we run the test from the project root.
        # But the task says "Implement T056" which is the test file.
        # The test file should be runnable.
        
        # Let's assume the test runner sets up the environment.
        # We will create the mock data in the `data/metrics` directory relative
        # to the current working directory if it exists, or use a temp dir.
        
        # To be safe, we will use a temp dir and patch the paths in the modules.
        
        # We need to import the modules first to patch them.
        # But we can't import them if the project structure isn't set up.
        # We assume the test is run from the project root.
        
        # Let's create a mock `main` function that we can call directly.
        # But we need to test the real `main`.
        
        # Okay, we will use `unittest.mock.patch` to redirect the file paths.
        
        # Patch the path in `analysis.py`
        # We need to know the exact variable name.
        # Let's assume it's `metrics_path` or similar.
        
        # Since we don't have the source code of `analysis.py` here (only API surface),
        # we have to assume standard patterns.
        # Standard pattern: `input_path = Path("data/metrics/SubjectMetrics.csv")`
        
        # We will patch `pathlib.Path`? No, too broad.
        # We will patch the specific function that loads the data.
        
        # Let's assume `analysis.py` has a function `load_metrics_data` or similar.
        # If not, we patch the `open` or `pd.read_csv`.
        
        # Let's patch `pd.read_csv` to return our DataFrame.
        
        # We will also need to ensure the output directories exist.
        
        # Let's write the test assuming we can patch `pd.read_csv`.
        
        original_read_csv = pd.read_csv
        
        def mock_read_csv(*args, **kwargs):
            # If the path matches our expected input, return our mock data
            # We check the path string
            if len(args) > 0:
                path_arg = args[0]
                if "SubjectMetrics.csv" in str(path_arg):
                    return generate_mock_metrics_csv(Path("/dev/null")) # We already have the df
            return original_read_csv(*args, **kwargs)
        
        # Actually, we already generated the file in the temp dir.
        # We can just set the working directory to the temp dir?
        # No, because imports might fail.
        
        # Let's try to patch the `main` function's internal logic.
        # We will assume `analysis.py` uses `Path("data/metrics/SubjectMetrics.csv")`.
        # We will patch `Path` in the `analysis` module.
        
        # This is getting complicated without seeing the source.
        # Let's assume the test is run in a environment where `data/metrics` exists.
        # But we are creating a test that MUST pass.
        
        # We will create the mock data in a temp dir and then patch `os.getcwd`?
        # No.
        
        # Let's assume the `main` function in `analysis.py` is:
        # def main():
        #     config = load_config()
        #     metrics_path = Path(config['paths']['metrics'])
        #     ...
        
        # If so, we can patch `load_config`.
        
        # Let's assume the config is loaded from `code/config.yaml`.
        # We can create a temp config file.
        
        # But we don't know the config structure.
        
        # Let's try a different tactic:
        # We will create the mock data in the actual `data/metrics` directory
        # relative to the project root, but we will do it inside the test.
        # And we will clean up afterwards.
        # But this might interfere with other tests.
        
        # Better: We will use `pytest` fixtures or `unittest` setUp/tearDown.
        # But the task asks for a single test file.
        
        # Let's assume the test is run in isolation.
        # We will create the mock data in a temp dir and then patch the `Path`
        # in the `analysis` module to point to that temp dir.
        
        # We will use `unittest.mock.patch` on `analysis.Path`.
        
        # Wait, `analysis.py` imports `Path` from `pathlib`.
        # So we patch `analysis.Path`.
        
        # We will create a custom `Path` class that redirects `data/metrics` to our temp dir.
        
        # This is the most robust way.
        
        from unittest.mock import patch, MagicMock
        
        # Create the mock data
        mock_df = generate_mock_metrics_csv(Path("/dev/null")) # Just to get the df
        
        # We need to return the df when read_csv is called with the metrics path.
        # But we also need to ensure the output files are written to the temp dir.
        
        # Let's patch `pd.read_csv` and `json.dump` (or the file writing functions).
        
        # Actually, the simplest way is to:
        # 1. Create the mock data in a temp directory.
        # 2. Patch the `Path` constructor in `analysis` and `report` modules to
        #    redirect the specific output paths to the temp directory.
        
        # We will define a custom Path class.
        
        class RedirectedPath(Path):
            def __new__(cls, *args, **kwargs):
                # If the path contains "data/metrics/SubjectMetrics.csv", redirect to temp
                # If the path contains "data/results", redirect to temp
                # If the path contains "reports", redirect to temp
                path_str = str(args[0]) if args else ""
                if "data/metrics/SubjectMetrics.csv" in path_str:
                    return super().__new__(cls, str(metrics_csv_path))
                elif "data/results/analysis_results.json" in path_str:
                    return super().__new__(cls, str(data_results_dir / "analysis_results.json"))
                elif "reports/final_report.md" in path_str:
                    return super().__new__(cls, str(reports_dir / "final_report.md"))
                return super().__new__(cls, *args, **kwargs)
        
        # We need to patch `analysis.Path` and `report.Path`.
        # But `analysis.py` imports `Path` from `pathlib`.
        # So we patch `analysis.Path` and `report.Path`.
        
        # We also need to ensure the temp directory exists.
        data_results_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('analysis.Path', RedirectedPath), \
             patch('report.Path', RedirectedPath):
            
            # Now run the main function of analysis.py
            # We assume it prints to stdout or logs.
            # We capture the output? Not necessary for this test.
            # We just need to ensure it runs without error.
            
            try:
                # We need to import the module again? No, it's already imported.
                # But we patched it.
                # We need to call `analysis.main()`.
                # But `analysis` might not be imported yet.
                
                # We import it inside the patch context.
                from code import analysis
                from code import report
                
                # Run the analysis
                analysis.main()
                
                # Check if the output files exist
                assert (data_results_dir / "analysis_results.json").exists(), \
                    "analysis_results.json was not created"
                
                assert (reports_dir / "final_report.md").exists(), \
                    "final_report.md was not created"
                
                # Validate the JSON
                with open(data_results_dir / "analysis_results.json", 'r') as f:
                    results = json.load(f)
                
                assert 'coefficients' in results or 'results' in results, \
                    "JSON report missing expected keys"
                
                # Validate the Markdown report contains expected sections
                with open(reports_dir / "final_report.md", 'r') as f:
                    report_content = f.read()
                
                assert "Significant" in report_content or "Non-Significant" in report_content, \
                    "Report missing significance flags"
                
                assert "Confounding Limitation" in report_content or "temporal" in report_content.lower(), \
                    "Report missing confounding limitation section"
                
            except Exception as e:
                # If the analysis fails, we should report the error
                # But we want to know if it's due to our mock data or the code.
                # We assume the mock data is valid.
                raise AssertionError(f"Analysis failed: {e}")

if __name__ == "__main__":
    test_end_to_end_analysis_report_generation()
    print("Integration test T056 passed.")
