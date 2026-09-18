"""
Validation script for the quickstart.md end-to-end reproducibility check.
This script verifies that the entire pipeline runs successfully and produces
the expected artifacts as documented in quickstart.md.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import Config, ensure_directories
from code.data.ingest import main as ingest_main
from code.data.preprocess import main as preprocess_main
from code.models.lmm import main as lmm_main
from code.reports.generate_report import main as report_main
from code.models.metrics import main as metrics_main
from code.viz.plots import main as viz_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'state' / 'validation.log')
    ]
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results."""
    def __init__(self, step: str, success: bool, message: str, details: Optional[Dict] = None):
        self.step = step
        self.success = success
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step': self.step,
            'success': self.success,
            'message': self.message,
            'details': self.details
        }


def validate_directory_structure() -> ValidationResult:
    """Validate that all required directories exist."""
    logger.info("Validating directory structure...")
    try:
        ensure_directories()
        required_dirs = [
            Config.DATA_RAW,
            Config.DATA_PROCESSED,
            Config.PRIMES,
            Config.TARGETS,
            PROJECT_ROOT / 'data' / 'processed',
            PROJECT_ROOT / 'figures',
            PROJECT_ROOT / 'reports',
            PROJECT_ROOT / 'state' / 'projects' / 'PROJ-345'
        ]

        missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]

        if missing_dirs:
            return ValidationResult(
                'directory_structure',
                False,
                f"Missing directories: {missing_dirs}",
                {'missing': missing_dirs}
            )

        return ValidationResult(
            'directory_structure',
            True,
            "All required directories exist.",
            {'verified': [str(d) for d in required_dirs]}
        )
    except Exception as e:
        return ValidationResult(
            'directory_structure',
            False,
            f"Error validating directories: {str(e)}",
            {'error': str(e)}
        )


def validate_data_ingestion() -> ValidationResult:
    """Validate that data ingestion produces expected artifacts."""
    logger.info("Validating data ingestion...")
    try:
        # Run ingestion
        logger.info("Running data ingestion...")
        ingest_main()

        # Check for expected outputs
        linked_trials_path = PROJECT_ROOT / 'data' / 'processed' / 'linked_trials.csv'
        ingest_metrics_path = PROJECT_ROOT / 'data' / 'processed' / 'ingest_metrics.json'

        if not linked_trials_path.exists():
            return ValidationResult(
                'data_ingestion',
                False,
                f"Missing artifact: {linked_trials_path}"
            )

        if not ingest_metrics_path.exists():
            return ValidationResult(
                'data_ingestion',
                False,
                f"Missing artifact: {ingest_metrics_path}"
            )

        # Validate CSV content
        df = pd.read_csv(linked_trials_path)
        required_columns = ['trial_id', 'response_time', 'stimulus_id', 'prime_condition', 'participant_id']
        missing_cols = [c for c in required_columns if c not in df.columns]

        if missing_cols:
            return ValidationResult(
                'data_ingestion',
                False,
                f"Missing columns in linked_trials.csv: {missing_cols}",
                {'expected_columns': required_columns, 'actual_columns': list(df.columns)}
            )

        if len(df) == 0:
            return ValidationResult(
                'data_ingestion',
                False,
                "linked_trials.csv is empty"
            )

        # Validate metrics JSON
        with open(ingest_metrics_path, 'r') as f:
            metrics = json.load(f)

        if 'linked_metadata_percentage' not in metrics:
            return ValidationResult(
                'data_ingestion',
                False,
                "Missing 'linked_metadata_percentage' in ingest_metrics.json"
            )

        return ValidationResult(
            'data_ingestion',
            True,
            f"Data ingestion successful. Processed {len(df)} trials.",
            {
                'trial_count': len(df),
                'metrics': metrics,
                'artifacts': [str(linked_trials_path), str(ingest_metrics_path)]
            }
        )
    except Exception as e:
        return ValidationResult(
            'data_ingestion',
            False,
            f"Error during data ingestion: {str(e)}",
            {'error': str(e)}
        )


def validate_preprocessing() -> ValidationResult:
    """Validate that preprocessing produces expected artifacts."""
    logger.info("Validating preprocessing...")
    try:
        # Run preprocessing
        logger.info("Running preprocessing...")
        preprocess_main()

        # Check for expected outputs
        stimulus_metadata_path = PROJECT_ROOT / 'data' / 'processed' / 'stimulus_metadata.csv'
        confounding_report_path = PROJECT_ROOT / 'data' / 'processed' / 'confounding_report.json'

        missing_artifacts = []
        if not stimulus_metadata_path.exists():
            missing_artifacts.append(str(stimulus_metadata_path))
        if not confounding_report_path.exists():
            missing_artifacts.append(str(confounding_report_path))

        if missing_artifacts:
            return ValidationResult(
                'preprocessing',
                False,
                f"Missing artifacts: {missing_artifacts}",
                {'missing': missing_artifacts}
            )

        # Validate stimulus metadata
        meta_df = pd.read_csv(stimulus_metadata_path)
        if 'valence' not in meta_df.columns:
            return ValidationResult(
                'preprocessing',
                False,
                "Missing 'valence' column in stimulus_metadata.csv"
            )

        if meta_df['valence'].isna().all():
            return ValidationResult(
                'preprocessing',
                False,
                "All valence values are null in stimulus_metadata.csv"
            )

        # Validate confounding report
        with open(confounding_report_path, 'r') as f:
            conf_report = json.load(f)

        if 'is_confounded' not in conf_report:
            return ValidationResult(
                'preprocessing',
                False,
                "Missing 'is_confounded' in confounding_report.json"
            )

        return ValidationResult(
            'preprocessing',
            True,
            f"Preprocessing successful. Processed {len(meta_df)} stimuli.",
            {
                'stimulus_count': len(meta_df),
                'is_confounded': conf_report.get('is_confounded'),
                'artifacts': [str(stimulus_metadata_path), str(confounding_report_path)]
            }
        )
    except Exception as e:
        return ValidationResult(
            'preprocessing',
            False,
            f"Error during preprocessing: {str(e)}",
            {'error': str(e)}
        )


def validate_modeling() -> ValidationResult:
    """Validate that modeling produces expected artifacts."""
    logger.info("Validating modeling...")
    try:
        # Run modeling
        logger.info("Running LMM analysis...")
        lmm_main()

        # Run metrics
        logger.info("Running metrics calculation...")
        metrics_main()

        # Check for expected outputs
        lmm_results_path = PROJECT_ROOT / 'data' / 'processed' / 'lmm_results.json'
        sensitivity_path = PROJECT_ROOT / 'data' / 'processed' / 'sensitivity_analysis.csv'
        convergence_path = PROJECT_ROOT / 'state' / 'model_convergence_metrics.json'

        missing_artifacts = []
        if not lmm_results_path.exists():
            missing_artifacts.append(str(lmm_results_path))
        if not sensitivity_path.exists():
            missing_artifacts.append(str(sensitivity_path))
        if not convergence_path.exists():
            missing_artifacts.append(str(convergence_path))

        if missing_artifacts:
            return ValidationResult(
                'modeling',
                False,
                f"Missing artifacts: {missing_artifacts}",
                {'missing': missing_artifacts}
            )

        # Validate LMM results
        with open(lmm_results_path, 'r') as f:
            lmm_results = json.load(f)

        if 'caution_note' not in lmm_results:
            return ValidationResult(
                'modeling',
                False,
                "Missing 'caution_note' in lmm_results.json"
            )

        if 'Associational analysis only; not causal' not in lmm_results['caution_note']:
            return ValidationResult(
                'modeling',
                False,
                "Missing causal caution in lmm_results.json"
            )

        # Validate sensitivity analysis
        sens_df = pd.read_csv(sensitivity_path)
        if 'alpha' not in sens_df.columns or 'significance_rate' not in sens_df.columns:
            return ValidationResult(
                'modeling',
                False,
                "Missing required columns in sensitivity_analysis.csv"
            )

        if len(sens_df) != 10:
            return ValidationResult(
                'modeling',
                False,
                f"sensitivity_analysis.csv should have 10 rows, found {len(sens_df)}"
            )

        expected_alphas = [i/100 for i in range(1, 11)]
        if not np.allclose(sorted(sens_df['alpha'].tolist()), sorted(expected_alphas)):
            return ValidationResult(
                'modeling',
                False,
                f"Alpha values in sensitivity_analysis.csv do not match expected range 0.01-0.10"
            )

        return ValidationResult(
            'modeling',
            True,
            "Modeling completed successfully.",
            {
                'artifacts': [str(lmm_results_path), str(sensitivity_path), str(convergence_path)],
                'sensitivity_rows': len(sens_df)
            }
        )
    except Exception as e:
        return ValidationResult(
            'modeling',
            False,
            f"Error during modeling: {str(e)}",
            {'error': str(e)}
        )


def validate_reporting() -> ValidationResult:
    """Validate that reporting produces expected artifacts."""
    logger.info("Validating reporting...")
    try:
        # Run visualization
        logger.info("Running visualization...")
        viz_main()

        # Run report generation
        logger.info("Running report generation...")
        report_main()

        # Check for expected outputs
        report_path = PROJECT_ROOT / 'reports' / 'final_report.pdf'
        interaction_plot_path = PROJECT_ROOT / 'figures' / 'interaction_plot.png'
        coefficient_table_path = PROJECT_ROOT / 'figures' / 'coefficient_table.png'

        missing_artifacts = []
        if not report_path.exists():
            missing_artifacts.append(str(report_path))
        if not interaction_plot_path.exists():
            missing_artifacts.append(str(interaction_plot_path))
        if not coefficient_table_path.exists():
            missing_artifacts.append(str(coefficient_table_path))

        if missing_artifacts:
            return ValidationResult(
                'reporting',
                False,
                f"Missing artifacts: {missing_artifacts}",
                {'missing': missing_artifacts}
            )

        # Validate report content (check for limitations section)
        # Note: We can't easily parse PDF content, but we check file size > 0
        if os.path.getsize(report_path) == 0:
            return ValidationResult(
                'reporting',
                False,
                "final_report.pdf is empty"
            )

        return ValidationResult(
            'reporting',
            True,
            "Reporting completed successfully.",
            {
                'artifacts': [str(report_path), str(interaction_plot_path), str(coefficient_table_path)],
                'report_size_bytes': os.path.getsize(report_path)
            }
        )
    except Exception as e:
        return ValidationResult(
            'reporting',
            False,
            f"Error during reporting: {str(e)}",
            {'error': str(e)}
        )


def run_full_pipeline() -> List[ValidationResult]:
    """Run the full validation pipeline."""
    logger.info("Starting full pipeline validation...")
    start_time = time.time()

    results = []

    # Step 1: Directory structure
    results.append(validate_directory_structure())

    # Step 2: Data ingestion
    if results[-1].success:
        results.append(validate_data_ingestion())

    # Step 3: Preprocessing
    if results[-1].success:
        results.append(validate_preprocessing())

    # Step 4: Modeling
    if results[-1].success:
        results.append(validate_modeling())

    # Step 5: Reporting
    if results[-1].success:
        results.append(validate_reporting())

    elapsed = time.time() - start_time
    logger.info(f"Pipeline validation completed in {elapsed:.2f} seconds.")

    return results


def main():
    """Main entry point for validation."""
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation for PROJ-345")
    logger.info("=" * 60)

    results = run_full_pipeline()

    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)

    success_count = sum(1 for r in results if r.success)
    total_count = len(results)

    for result in results:
        status = "✓ PASS" if result.success else "✗ FAIL"
        logger.info(f"[{status}] {result.step}: {result.message}")

    logger.info("-" * 60)
    logger.info(f"Total: {success_count}/{total_count} steps passed")

    if success_count == total_count:
        logger.info("✓ ALL VALIDATIONS PASSED - Pipeline is reproducible!")
        # Write final report
        report_path = PROJECT_ROOT / 'state' / 'validation_report.json'
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'total_steps': total_count,
                'passed_steps': success_count,
                'results': [r.to_dict() for r in results]
            }, f, indent=2)
        logger.info(f"Validation report saved to {report_path}")
        sys.exit(0)
    else:
        logger.error(f"✗ VALIDATION FAILED - {total_count - success_count} step(s) failed")
        # Write failure report
        report_path = PROJECT_ROOT / 'state' / 'validation_report.json'
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'total_steps': total_count,
                'passed_steps': success_count,
                'results': [r.to_dict() for r in results]
            }, f, indent=2)
        logger.info(f"Validation report saved to {report_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()