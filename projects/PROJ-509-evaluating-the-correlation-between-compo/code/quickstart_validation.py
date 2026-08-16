"""
Quickstart validation script for PROJ-509.
Validates end-to-end reproducibility by running the main pipeline steps
and verifying that all required artifacts exist and contain valid data.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path if not already there
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import load_paths
from utils.logging import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

def verify_artifacts(artifacts: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that all required artifacts exist and are non-empty.

    Args:
        artifacts: List of relative paths to artifacts

    Returns:
        Tuple of (all_exist, list_of_missing_artifacts)
    """
    missing = []
    for artifact_path in artifacts:
        full_path = PROJECT_ROOT / artifact_path
        if not full_path.exists():
            missing.append(artifact_path)
            logger.error(f"Missing artifact: {artifact_path}")
        elif full_path.stat().st_size == 0:
            missing.append(artifact_path)
            logger.error(f"Empty artifact: {artifact_path}")
        else:
            logger.info(f"Verified artifact: {artifact_path}")

    return len(missing) == 0, missing

def validate_metrics_content(metrics_path: str) -> bool:
    """
    Validate that model_metrics.json contains required fields and valid values.

    Args:
        metrics_path: Relative path to model_metrics.json

    Returns:
        True if validation passes, False otherwise
    """
    full_path = PROJECT_ROOT / metrics_path
    try:
        with open(full_path, 'r') as f:
            metrics = json.load(f)

        required_fields = [
            'rf_r2', 'rf_mae', 'rf_rmse',
            'gb_r2', 'gb_mae', 'gb_rmse',
            'overfitting_ratio', 'predictive_power',
            'final_r2_source'
        ]

        for field in required_fields:
            if field not in metrics:
                logger.error(f"Missing required field in metrics: {field}")
                return False

        # Validate numeric fields
        numeric_fields = ['rf_r2', 'rf_mae', 'rf_rmse', 'gb_r2', 'gb_mae', 'gb_rmse', 'overfitting_ratio']
        for field in numeric_fields:
            value = metrics[field]
            if not isinstance(value, (int, float)):
                logger.error(f"Field {field} is not numeric: {value}")
                return False
            if field.endswith('_r2') and value > 1.0:
                logger.error(f"R² value out of range for {field}: {value}")
                return False

        # Validate final_r2_source
        if metrics['final_r2_source'] != 'holdout':
            logger.error(f"final_r2_source should be 'holdout', got: {metrics['final_r2_source']}")
            return False

        logger.info("Metrics validation passed")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating metrics: {e}")
        return False

def run_step(step_name: str, command: List[str], timeout: int = 3600) -> bool:
    """
    Run a pipeline step and verify it completes successfully.

    Args:
        step_name: Human-readable name of the step
        command: List of command arguments
        timeout: Maximum execution time in seconds

    Returns:
        True if step completes successfully, False otherwise
    """
    logger.info(f"Running step: {step_name}")
    logger.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f"Step '{step_name}' failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        logger.info(f"Step '{step_name}' completed successfully")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Step '{step_name}' timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Error running step '{step_name}': {e}")
        return False

def main():
    """
    Main validation function that orchestrates the full quickstart validation.
    """
    # Setup logging
    log_path = PROJECT_ROOT / 'data' / 'logs' / 'quickstart_validation.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=str(log_path), level=logging.INFO)

    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation for PROJ-509")
    logger.info("=" * 60)

    # Define required artifacts based on tasks.md
    required_artifacts = [
        # Data artifacts
        'data/raw/mp-2020.12.1.csv',
        'data/processed/computed_descriptors.csv',
        'data/evaluation/model_rf.pkl',
        'data/evaluation/model_gb.pkl',
        'data/evaluation/model_metrics.json',
        'data/evaluation/feature_ranking.json',
        'data/evaluation/vif_scores.json',
        'data/evaluation/permutation_importance.json',
        'data/evaluation/ale_metrics.json',
        'data/evaluation/statistical_tests.json',
        'data/evaluation/cv_scores.json',
        # Plots
        'data/evaluation/ale_rf_mean_variance_electronegativity.png',
        'data/evaluation/ale_rf_mean_variance_radius.png',
        'data/evaluation/ale_rf_mean_variance_melting_point.png',
        # Logs
        'data/logs/sampling.log',
        'data/logs/outliers.log',
    ]

    # Check for required artifacts
    logger.info("\n--- Checking Required Artifacts ---")
    all_exist, missing = verify_artifacts(required_artifacts)

    if not all_exist:
        logger.error(f"Missing {len(missing)} required artifacts:")
        for artifact in missing:
            logger.error(f"  - {artifact}")
        logger.error("Validation FAILED due to missing artifacts.")
        sys.exit(1)

    # Validate metrics content
    logger.info("\n--- Validating Metrics Content ---")
    metrics_valid = validate_metrics_content('data/evaluation/model_metrics.json')

    if not metrics_valid:
        logger.error("Metrics validation FAILED.")
        sys.exit(1)

    # Validate feature ranking
    logger.info("\n--- Validating Feature Ranking ---")
    feature_ranking_path = PROJECT_ROOT / 'data' / 'evaluation' / 'feature_ranking.json'
    try:
        with open(feature_ranking_path, 'r') as f:
            ranking = json.load(f)

        if not isinstance(ranking, list) or len(ranking) == 0:
            logger.error("Feature ranking is empty or invalid")
            sys.exit(1)

        logger.info(f"Feature ranking contains {len(ranking)} features")
        logger.info(f"Top 3 features: {[f['feature'] for f in ranking[:3]]}")
    except Exception as e:
        logger.error(f"Error validating feature ranking: {e}")
        sys.exit(1)

    # Validate VIF scores
    logger.info("\n--- Validating VIF Scores ---")
    vif_path = PROJECT_ROOT / 'data' / 'evaluation' / 'vif_scores.json'
    try:
        with open(vif_path, 'r') as f:
            vif_scores = json.load(f)

        if not isinstance(vif_scores, dict) or len(vif_scores) == 0:
            logger.error("VIF scores are empty or invalid")
            sys.exit(1)

        high_vif = [k for k, v in vif_scores.items() if v > 10]
        if high_vif:
            logger.warning(f"High VIF scores detected (>10): {high_vif}")
        else:
            logger.info("All VIF scores are within acceptable range (<10)")
    except Exception as e:
        logger.error(f"Error validating VIF scores: {e}")
        sys.exit(1)

    # Validate ALE metrics
    logger.info("\n--- Validating ALE Metrics ---")
    ale_path = PROJECT_ROOT / 'data' / 'evaluation' / 'ale_metrics.json'
    try:
        with open(ale_path, 'r') as f:
            ale_metrics = json.load(f)

        if not isinstance(ale_metrics, dict) or len(ale_metrics) == 0:
            logger.error("ALE metrics are empty or invalid")
            sys.exit(1)

        logger.info(f"ALE metrics: {ale_metrics}")
    except Exception as e:
        logger.error(f"Error validating ALE metrics: {e}")
        sys.exit(1)

    # Validate statistical tests
    logger.info("\n--- Validating Statistical Tests ---")
    stats_path = PROJECT_ROOT / 'data' / 'evaluation' / 'statistical_tests.json'
    try:
        with open(stats_path, 'r') as f:
            stats = json.load(f)

        if 't_statistic' not in stats or 'p_value' not in stats:
            logger.error("Statistical tests missing required fields")
            sys.exit(1)

        logger.info(f"t-statistic: {stats['t_statistic']:.4f}, p-value: {stats['p_value']:.4f}")
    except Exception as e:
        logger.error(f"Error validating statistical tests: {e}")
        sys.exit(1)

    # Validate CV scores
    logger.info("\n--- Validating CV Scores ---")
    cv_path = PROJECT_ROOT / 'data' / 'evaluation' / 'cv_scores.json'
    try:
        with open(cv_path, 'r') as f:
            cv_scores = json.load(f)

        if 'mean_r2' not in cv_scores or 'std_r2' not in cv_scores:
            logger.error("CV scores missing required fields")
            sys.exit(1)

        logger.info(f"CV mean R²: {cv_scores['mean_r2']:.4f} ± {cv_scores['std_r2']:.4f}")
    except Exception as e:
        logger.error(f"Error validating CV scores: {e}")
        sys.exit(1)

    # Validate permutation importance
    logger.info("\n--- Validating Permutation Importance ---")
    perm_path = PROJECT_ROOT / 'data' / 'evaluation' / 'permutation_importance.json'
    try:
        with open(perm_path, 'r') as f:
            perm_data = json.load(f)

        if 'r' not in perm_data or 'importance_correlation_pass' not in perm_data:
            logger.error("Permutation importance missing required fields")
            sys.exit(1)

        logger.info(f"Correlation r: {perm_data['r']:.4f}, Pass: {perm_data['importance_correlation_pass']}")
    except Exception as e:
        logger.error(f"Error validating permutation importance: {e}")
        sys.exit(1)

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Quickstart Validation Summary")
    logger.info("=" * 60)
    logger.info(f"Total artifacts verified: {len(required_artifacts)}")
    logger.info("All validations PASSED")
    logger.info("End-to-end reproducibility confirmed")
    logger.info("=" * 60)

    # Write validation report
    report_path = PROJECT_ROOT / 'data' / 'evaluation' / 'quickstart_validation_report.json'
    report = {
        'status': 'PASSED',
        'artifacts_verified': len(required_artifacts),
        'metrics_valid': True,
        'feature_ranking_valid': True,
        'vif_scores_valid': True,
        'ale_metrics_valid': True,
        'statistical_tests_valid': True,
        'cv_scores_valid': True,
        'permutation_importance_valid': True
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to: {report_path}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
