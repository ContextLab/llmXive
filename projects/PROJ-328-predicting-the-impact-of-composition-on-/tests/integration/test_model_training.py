"""
Integration test for the model training pipeline (T021).

This test verifies the end-to-end execution of the model training workflow:
1. Loads cleaned data from data/processed/solder_hardness_cleaned.csv
2. Runs feature engineering (CLR transform + Physical Descriptors)
3. Trains XGBoost and Linear Regression models (CPU-only)
4. Performs Cross-Validation
5. Performs Bootstrap analysis
6. Performs SHAP analysis
7. Verifies all required output artifacts are generated with valid content.

CRITICAL: This test uses REAL data. If the cleaned dataset is missing or empty,
the test will fail loudly to prevent fabrication.
"""
import os
import sys
import pytest
import subprocess
import json
import yaml
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Any

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for paths (relative to project root)
DATA_PROCESSED_DIR = project_root / "data" / "processed"
DATA_OUTPUTS_DIR = project_root / "data" / "outputs"
CODE_DIR = project_root / "code"

REQUIRED_ARTIFACTS = [
    DATA_PROCESSED_DIR / "clr_features.csv",
    DATA_PROCESSED_DIR / "descriptors.csv",
    DATA_PROCESSED_DIR / "cv_results.json",
    DATA_PROCESSED_DIR / "xgboost_model.pkl",
    DATA_PROCESSED_DIR / "linear_model.pkl",
    DATA_PROCESSED_DIR / "shap_ranking.yaml",
    DATA_PROCESSED_DIR / "test_set_ci.yaml",
    DATA_PROCESSED_DIR / "paired_ttest_results.yaml",
    DATA_PROCESSED_DIR / "sensitivity_analysis.yaml",
    DATA_PROCESSED_DIR / "vif_report.yaml",
]

def check_cleaned_data_exists():
    """Verify the input cleaned dataset exists and has rows."""
    cleaned_file = DATA_PROCESSED_DIR / "solder_hardness_cleaned.csv"
    if not cleaned_file.exists():
        pytest.fail(f"CRITICAL: Input file {cleaned_file} does not exist. "
                    "The ingestion pipeline (T013) must run before this test.")
    
    df = pd.read_csv(cleaned_file)
    if len(df) == 0:
        pytest.fail(f"CRITICAL: Input file {cleaned_file} is empty. "
                    "Real data ingestion failed or filtered out all records.")
    logger.info(f"Found {len(df)} rows in cleaned data. Proceeding with integration test.")
    return df

def run_script(script_path: Path, env_vars: Dict[str, str] = None) -> subprocess.CompletedProcess:
    """Run a Python script and capture output."""
    cmd = [sys.executable, str(script_path)]
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout for training
    )
    
    if result.returncode != 0:
        logger.error(f"STDOUT:\n{result.stdout}")
        logger.error(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Script failed: {script_path.name}\n{result.stderr}")
    
    return result

def validate_artifact_exists(path: Path):
    """Assert an artifact exists and is not empty."""
    if not path.exists():
        pytest.fail(f"Artifact missing: {path}")
    
    size = path.stat().st_size
    if size == 0:
        pytest.fail(f"Artifact is empty: {path}")
    
    # Validate JSON/YAML structure if applicable
    if path.suffix == '.json':
        try:
            with open(path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {path}: {e}")
    elif path.suffix in ['.yaml', '.yml']:
        try:
            with open(path, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {path}: {e}")

@pytest.mark.integration
def test_model_training_pipeline_end_to_end():
    """
    End-to-end integration test for the model training pipeline.
    
    Steps:
    1. Verify input data exists (T013 output).
    2. Run Feature Engineering (T023b, T023c).
    3. Run VIF Calculation (T024).
    4. Run XGBoost Training (T025).
    5. Run Linear Regression Training (T026).
    6. Run Cross-Validation (T027).
    7. Run Bootstrap Analysis (T028, T029b).
    8. Run SHAP Analysis (T030).
    9. Verify all outputs exist and contain valid data.
    """
    
    # Step 1: Check Input Data
    check_cleaned_data_exists()
    
    # Step 2: Feature Engineering
    # Run Descriptor Engine (handles both CLR and Physical Descriptors)
    # Based on API surface: code/features/descriptor_engine_main.py
    descriptor_script = CODE_DIR / "features" / "descriptor_engine_main.py"
    if descriptor_script.exists():
        run_script(descriptor_script)
    else:
        # Fallback if main entry point is missing, try the module directly
        # Assuming the module has a main() function we can call via python -m or similar
        # But based on API, we assume the script exists. If not, fail.
        pytest.fail(f"Feature engineering script not found: {descriptor_script}")
    
    # Step 3: VIF Calculation
    vif_script = CODE_DIR / "features" / "collinearity.py"
    if vif_script.exists():
        run_script(vif_script)
    else:
        logger.warning("VIF script not found, skipping VIF step (may cause downstream failures).")
    
    # Step 4 & 5: Model Training (XGBoost & Linear)
    # Run XGBoost
    xgb_script = CODE_DIR / "models" / "xgboost_trainer.py"
    if xgb_script.exists():
        run_script(xgb_script)
    else:
        pytest.fail(f"XGBoost trainer script not found: {xgb_script}")
    
    # Run Linear Regression
    lin_script = CODE_DIR / "models" / "linear_trainer.py"
    if lin_script.exists():
        run_script(lin_script)
    else:
        pytest.fail(f"Linear Regression trainer script not found: {lin_script}")
    
    # Step 6: Cross-Validation
    cv_script = CODE_DIR / "evaluation" / "cv.py"
    if cv_script.exists():
        run_script(cv_script)
    else:
        pytest.fail(f"CV script not found: {cv_script}")
    
    # Step 7: Bootstrap Analysis
    bootstrap_script = CODE_DIR / "evaluation" / "bootstrap.py"
    if bootstrap_script.exists():
        run_script(bootstrap_script)
    else:
        pytest.fail(f"Bootstrap script not found: {bootstrap_script}")
    
    # Step 8: SHAP Analysis
    shap_script = CODE_DIR / "evaluation" / "shap_analysis.py"
    if shap_script.exists():
        run_script(shap_script)
    else:
        pytest.fail(f"SHAP script not found: {shap_script}")
    
    # Step 9: Sensitivity Analysis (if applicable)
    # This might depend on bootstrap results
    sensitivity_script = CODE_DIR / "evaluation" / "sensitivity.py"
    if sensitivity_script.exists():
        try:
            run_script(sensitivity_script)
        except RuntimeError as e:
            # Sensitivity might fail if bootstrap didn't produce enough samples
            logger.warning(f"Sensitivity analysis failed (expected if data is small): {e}")
    
    # Step 10: Verify Artifacts
    logger.info("Verifying generated artifacts...")
    missing_artifacts = []
    invalid_artifacts = []
    
    for artifact in REQUIRED_ARTIFACTS:
        try:
            validate_artifact_exists(artifact)
            logger.info(f"  OK: {artifact.name}")
        except AssertionError as e:
            missing_artifacts.append(str(artifact))
            logger.error(f"  FAIL: {artifact.name} - {e}")
    
    if missing_artifacts:
        pytest.fail(f"Integration test failed. Missing or invalid artifacts:\n" + "\n".join(missing_artifacts))
    
    # Additional content validation for key files
    # Check that test_set_ci.yaml has required keys
    ci_file = DATA_PROCESSED_DIR / "test_set_ci.yaml"
    if ci_file.exists():
        with open(ci_file, 'r') as f:
            ci_data = yaml.safe_load(f)
        required_keys = ['r2_mean', 'r2_ci_lower', 'r2_ci_upper', 'rmse_mean', 'rmse_ci_lower', 'rmse_ci_upper']
        missing_keys = [k for k in required_keys if k not in ci_data]
        if missing_keys:
            pytest.fail(f"test_set_ci.yaml missing keys: {missing_keys}")
    
    # Check paired_ttest_results.yaml
    ttest_file = DATA_PROCESSED_DIR / "paired_ttest_results.yaml"
    if ttest_file.exists():
        with open(ttest_file, 'r') as f:
            ttest_data = yaml.safe_load(f)
        required_keys = ['t_statistic', 'p_value', 'significant']
        missing_keys = [k for k in required_keys if k not in ttest_data]
        if missing_keys:
            pytest.fail(f"paired_ttest_results.yaml missing keys: {missing_keys}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
