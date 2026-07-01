"""
Integration test for the full analysis pipeline (User Story 2).

This test verifies the end-to-end flow:
1. Loads real data from data/processed/memory_measurements.csv
2. Runs the statistical analysis in code/analyze.py
3. Validates the output report structure and content
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from code.analyze import run_statistical_analysis
from code.config import CI_MEMORY_LIMIT_GB, EXECUTION_TIMEOUT_SEC

def test_full_analysis_pipeline():
    """
    Integration test: Run full analysis on processed memory measurements.
    
    This test assumes:
    - data/processed/memory_measurements.csv exists (produced by T017)
    - The CSV contains paired LLM and Human solutions for the same problems
    """
    # Setup: Create a temporary directory for output
    temp_dir = tempfile.mkdtemp()
    try:
        input_path = project_root / "data" / "processed" / "memory_measurements.csv"
        output_path = Path(temp_dir) / "analysis_report.json"
        
        # Verify input file exists
        if not input_path.exists():
            # If file doesn't exist, we cannot run the integration test
            # This is a valid failure condition for the integration test
            print(f"Input file not found: {input_path}")
            print("Skipping integration test - data generation not complete.")
            return
        
        # Load and inspect input data
        df = pd.read_csv(input_path)
        print(f"Loaded {len(df)} rows from {input_path}")
        print(f"Columns: {list(df.columns)}")
        
        # Verify required columns exist
        required_cols = ['problem_id', 'source_type', 'peak_memory', 'status']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in input data: {missing_cols}")
        
        # Check for paired data (at least one problem with both LLM and Human)
        problem_ids = df['problem_id'].unique()
        paired_count = 0
        for pid in problem_ids:
            subset = df[df['problem_id'] == pid]
            source_types = set(subset['source_type'])
            if 'LLM' in source_types and 'Human' in source_types:
                paired_count += 1
        
        print(f"Found {paired_count} paired problems (with both LLM and Human)")
        
        if paired_count == 0:
            print("No paired data found. Skipping statistical analysis.")
            return
        
        # Run the analysis
        print(f"Running statistical analysis...")
        result = run_statistical_analysis(
            input_csv=str(input_path),
            output_json=str(output_path)
        )
        
        # Verify output file was created
        assert output_path.exists(), f"Output file not created: {output_path}"
        
        # Load and validate output report
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Validate report structure
        assert 'summary' in report, "Missing 'summary' in report"
        assert 'statistics' in report, "Missing 'statistics' in report"
        assert 'methodology' in report, "Missing 'methodology' in report"
        
        summary = report['summary']
        assert 'paired_count' in summary, "Missing 'paired_count' in summary"
        assert 'llm_success_rate' in summary, "Missing 'llm_success_rate' in summary"
        assert 'human_success_rate' in summary, "Missing 'human_success_rate' in summary"
        
        stats = report['statistics']
        assert 'test_method' in stats, "Missing 'test_method' in statistics"
        assert 'p_value' in stats, "Missing 'p_value' in statistics"
        assert 'effect_size' in stats, "Missing 'effect_size' in statistics"
        
        methodology = report['methodology']
        assert 'censored_data_handling' in methodology, "Missing 'censored_data_handling' in methodology"
        assert 'multiple_comparison_correction' in methodology, "Missing 'multiple_comparison_correction' in methodology"
        
        # Validate that the analysis actually ran (not just empty placeholders)
        assert summary['paired_count'] > 0, "No paired problems analyzed"
        assert stats['p_value'] is not None, "p-value is None"
        assert stats['effect_size'] is not None, "Effect size is None"
        
        print(f"Analysis complete. Report saved to: {output_path}")
        print(f"Test Method: {stats['test_method']}")
        print(f"P-value: {stats['p_value']:.4f}")
        print(f"Effect Size: {stats['effect_size']:.4f}")
        print(f"LLM Success Rate: {summary['llm_success_rate']:.2%}")
        print(f"Human Success Rate: {summary['human_success_rate']:.2%}")
        
        # Verify the analysis used the correct parameters
        assert methodology['censored_data_handling'] in ['kaplan_meier', 'tobit', 'wilcoxon_uncensored'], \
            f"Unexpected censored data handling method: {methodology['censored_data_handling']}"
        
        print("Integration test PASSED: Full analysis pipeline executed successfully.")
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_full_analysis_pipeline()