"""
End-to-end integration test for the herbivore resistance prediction pipeline.
Executes the full run-book sequence and verifies all declared artifacts exist.
"""
import os
import sys
import subprocess
import json
import pytest
from pathlib import Path

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Required artifacts based on task descriptions and execution failures
REQUIRED_ARTIFACTS = [
    # Raw data
    DATA_DIR / "raw" / "raw_dataset.csv",
    DATA_DIR / "raw" / "raw_dataset.csv.sha256",
    
    # Interim data
    DATA_DIR / "interim" / "harmonized.csv",
    DATA_DIR / "interim" / "ordinal_mapping.json",
    DATA_DIR / "interim" / "split_indices.json",
    DATA_DIR / "interim" / "split_log.txt",
    DATA_DIR / "interim" / "correlations.csv",
    DATA_DIR / "interim" / "null_distribution.csv",
    DATA_DIR / "interim" / "permutation_p_value.json",
    DATA_DIR / "interim" / "permutation_run.log",
    
    # Processed data
    DATA_DIR / "processed" / "pca_reduced.csv",
    DATA_DIR / "processed" / "model.pkl",
    DATA_DIR / "processed" / "model_metrics.json",
    DATA_DIR / "processed" / "feature_importance.csv",
    DATA_DIR / "processed" / "significant_biomarkers.csv",
    
    # Results
    RESULTS_DIR / "summary_report.md",
    RESULTS_DIR / "feasibility_report.json",
]

# Run-book commands to execute (in order)
RUN_BOOK_COMMANDS = [
    # 1. Setup directories (if not already done, but safe to run)
    ["python", str(CODE_DIR / "setup_directories.py")],
    
    # 2. Ingest data
    ["python", str(CODE_DIR / "ingest.py"), "--accession", "GSE12345", "--output", str(DATA_DIR / "raw")],
    
    # 3. Preprocess data
    ["python", str(CODE_DIR / "preprocess.py"), "--input", str(DATA_DIR / "raw" / "GSE12345_raw.csv"), "--output", str(DATA_DIR / "processed")],
    
    # 4. Train model
    ["python", str(CODE_DIR / "model.py"), "--input", str(DATA_DIR / "processed" / "GSE12345_processed.csv"), "--output", str(DATA_DIR / "processed")],
    
    # 5. Validate model
    ["python", str(CODE_DIR / "validation.py"), "--input", str(DATA_DIR / "processed" / "GSE12345_processed.csv"), "--model", str(DATA_DIR / "processed" / "GSE12345_model.pkl"), "--output", str(DATA_DIR / "processed")],
    
    # 6. Generate report
    ["python", str(CODE_DIR / "report.py"), "--input", str(DATA_DIR / "processed"), "--output", str(RESULTS_DIR)],
]

@pytest.fixture(scope="module")
def run_pipeline():
    """Execute the full pipeline run-book."""
    os.chdir(PROJECT_ROOT)
    
    for i, cmd in enumerate(RUN_BOOK_COMMANDS):
        print(f"\n--- Executing step {i+1}: {' '.join(cmd)} ---")
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes per step
            )
            
            if result.returncode != 0:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                pytest.fail(f"Pipeline step {i+1} failed with return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            pytest.fail(f"Pipeline step {i+1} timed out")
        except Exception as e:
            pytest.fail(f"Pipeline step {i+1} raised exception: {str(e)}")

def test_pipeline_execution(run_pipeline):
    """Verify the pipeline executed successfully (already checked in fixture)."""
    pass

def test_required_artifacts_exist():
    """Verify all declared deliverables are present on disk."""
    missing = []
    for artifact in REQUIRED_ARTIFACTS:
        if not artifact.exists():
            missing.append(str(artifact.relative_to(PROJECT_ROOT)))
    
    if missing:
        pytest.fail(f"Missing required artifacts:\n" + "\n".join(missing))

def test_artifacts_have_content():
    """Verify artifacts are not empty files."""
    empty_artifacts = []
    
    # Check CSV files
    csv_files = [
        DATA_DIR / "raw" / "raw_dataset.csv",
        DATA_DIR / "interim" / "harmonized.csv",
        DATA_DIR / "processed" / "pca_reduced.csv",
        DATA_DIR / "processed" / "feature_importance.csv",
        DATA_DIR / "processed" / "significant_biomarkers.csv",
        DATA_DIR / "interim" / "correlations.csv",
        DATA_DIR / "interim" / "null_distribution.csv",
    ]
    
    for csv_file in csv_files:
        if csv_file.exists() and csv_file.stat().st_size == 0:
            empty_artifacts.append(str(csv_file.relative_to(PROJECT_ROOT)))
    
    # Check JSON files
    json_files = [
        DATA_DIR / "interim" / "ordinal_mapping.json",
        DATA_DIR / "interim" / "split_indices.json",
        DATA_DIR / "interim" / "permutation_p_value.json",
        DATA_DIR / "processed" / "model_metrics.json",
        RESULTS_DIR / "feasibility_report.json",
    ]
    
    for json_file in json_files:
        if json_file.exists() and json_file.stat().st_size == 0:
            empty_artifacts.append(str(json_file.relative_to(PROJECT_ROOT)))
    
    # Check text files
    text_files = [
        DATA_DIR / "interim" / "split_log.txt",
        DATA_DIR / "interim" / "permutation_run.log",
        RESULTS_DIR / "summary_report.md",
    ]
    
    for text_file in text_files:
        if text_file.exists() and text_file.stat().st_size == 0:
            empty_artifacts.append(str(text_file.relative_to(PROJECT_ROOT)))
    
    if empty_artifacts:
        pytest.fail(f"Empty artifacts found:\n" + "\n".join(empty_artifacts))

def test_model_metrics_valid():
    """Verify model_metrics.json contains expected keys."""
    metrics_file = DATA_DIR / "processed" / "model_metrics.json"
    if not metrics_file.exists():
        pytest.skip("Model metrics file not found")
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    required_keys = ['r2_score', 'mse']
    missing_keys = [k for k in required_keys if k not in metrics]
    
    if missing_keys:
        pytest.fail(f"Model metrics missing required keys: {missing_keys}")

def test_feasibility_report_valid():
    """Verify feasibility_report.json contains expected structure."""
    report_file = RESULTS_DIR / "feasibility_report.json"
    if not report_file.exists():
        pytest.skip("Feasibility report not found")
    
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    required_keys = ['runtime_hours', 'peak_memory_gb', 'status']
    missing_keys = [k for k in required_keys if k not in report]
    
    if missing_keys:
        pytest.fail(f"Feasibility report missing required keys: {missing_keys}")
    
    if report['status'] not in ['PASS', 'FAIL']:
        pytest.fail(f"Feasibility report status invalid: {report['status']}")

def test_summary_report_contains_results():
    """Verify summary_report.md contains key results."""
    report_file = RESULTS_DIR / "summary_report.md"
    if not report_file.exists():
        pytest.skip("Summary report not found")
    
    with open(report_file, 'r') as f:
        content = f.read()
    
    required_strings = ['R²', 'MSE']
    missing_strings = [s for s in required_strings if s not in content]
    
    if missing_strings:
        pytest.fail(f"Summary report missing required content: {missing_strings}")

def test_feature_importance_has_metabolites():
    """Verify feature_importance.csv has metabolite data."""
    file_path = DATA_DIR / "processed" / "feature_importance.csv"
    if not file_path.exists():
        pytest.skip("Feature importance file not found")
    
    import pandas as pd
    df = pd.read_csv(file_path)
    
    required_columns = ['metabolite_name', 'importance_score']
    missing_columns = [c for c in required_columns if c not in df.columns]
    
    if missing_columns:
        pytest.fail(f"Feature importance missing columns: {missing_columns}")
    
    if len(df) == 0:
        pytest.fail("Feature importance file is empty")

def test_harmonized_data_has_resistance():
    """Verify harmonized.csv has resistance column with numeric values."""
    file_path = DATA_DIR / "interim" / "harmonized.csv"
    if not file_path.exists():
        pytest.skip("Harmonized data not found")
    
    import pandas as pd
    df = pd.read_csv(file_path)
    
    if 'resistance' not in df.columns:
        pytest.fail("Harmonized data missing 'resistance' column")
    
    # Check that resistance values are numeric (1, 2, 3 if ordinal conversion applied)
    if not pd.api.types.is_numeric_dtype(df['resistance']):
        pytest.fail("Resistance column is not numeric")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])