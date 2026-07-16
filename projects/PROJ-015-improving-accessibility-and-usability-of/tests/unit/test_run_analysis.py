import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.run_analysis import main
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import generate_metrics_summary

def create_test_data(tmp_path):
    """Creates dummy JSON session files for testing."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    sessions = []
    # Create 10 participants, each with 2 sessions (Traditional, Explainable)
    for i in range(10):
        for j, iface in enumerate(['Traditional', 'Explainable']):
            session = {
                "session_id": f"sess_{i}_{j}",
                "participant_id": f"part_{i}",
                "disability_type": "visual",
                "interface_type": iface,
                "sequence": "AB" if j == 0 else "BA",
                "completion_time": np.random.uniform(10, 60),
                "error_count": np.random.randint(0, 5),
                "explanation_engagement_time_seconds": np.random.uniform(5, 30),
                "sus_score": np.random.uniform(20, 100),
                "status": "complete"
            }
            sessions.append(session)
            
            # Write JSON
            with open(raw_dir / f"{session['session_id']}.json", 'w') as f:
                json.dump(session, f)
    
    return raw_dir, processed_dir

def test_run_analysis_pipeline(tmp_path):
    """
    Tests the full run_analysis.py pipeline.
    Verifies that metrics_summary.csv and report_summary.txt are generated.
    """
    raw_dir, processed_dir = create_test_data(tmp_path)
    
    # Mock command line arguments
    input_csv = processed_dir / "cleaned_sessions.csv"
    output_csv = processed_dir / "metrics_summary.csv"
    output_report = processed_dir / "report_summary.txt"
    
    # We need to simulate the CLI call or call main with patched args
    # Since main() uses argparse, we can't easily pass args directly without mocking sys.argv
    # Let's test the components directly to ensure the pipeline logic works
    
    # 1. Clean Data
    cleaner = DataCleaner()
    df_clean = cleaner.process_all_sessions(raw_dir, processed_dir)
    assert df_clean is not None, "Data cleaning failed"
    assert len(df_clean) > 0, "No data after cleaning"
    df_clean.to_csv(input_csv, index=False)
    
    # 2. Generate Metrics
    success = generate_metrics_summary(str(input_csv), str(output_csv))
    assert success, "Metrics generation failed"
    assert output_csv.exists(), "metrics_summary.csv not created"
    
    # 3. Check Report Generation (via ReportGenerator directly)
    from analysis.report_generator import ReportGenerator
    reporter = ReportGenerator()
    reporter.generate_report(str(input_csv), str(output_csv), str(output_report))
    assert output_report.exists(), "report_summary.txt not created"
    
    # 4. Verify content of metrics_summary.csv
    df_metrics = pd.read_csv(output_csv)
    required_cols = ['metric', 'f_statistic', 'p_value', 'adjusted_p_value', 'effect_size_eta2']
    for col in required_cols:
        assert col in df_metrics.columns, f"Missing column {col} in metrics_summary.csv"
    
    # 5. Verify content of report_summary.txt
    with open(output_report, 'r') as f:
        content = f.read()
    assert "Analysis Report Summary" in content
    assert "Statistical Results" in content