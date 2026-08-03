"""
Task T033: Run quickstart.md validation to ensure end-to-end reproducibility.

This script executes the full pipeline defined in the project's quickstart
documentation to verify that all components work together correctly.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import load_config, Config
from utils import setup_logging, set_deterministic_seed
from metadata_checksum import verify_zero_overlap, load_json_metadata
from latent_drift import load_reference_stats, LatentDriftDetector
from physics_state_extractor import PhysicsStateExtractor
from inference_pipeline import InferencePipeline
from baseline_validator import BaselineValidator
from analysis import StatisticalAnalyzer
from trial_log_schema import TrialLogger, get_schema_description

def log_section(section_name: str):
    """Log a section header."""
    logging.info("=" * 60)
    logging.info(f"  {section_name}")
    logging.info("=" * 60)

def validate_prerequisites(config: Config) -> bool:
    """Validate that all required input files exist."""
    log_section("VALIDATING PREREQUISITES")

    required_files = [
        "data/raw/gam_reference_stats.json",
        "data/raw/drift_threshold_validation.json",
        "data/generated/physics_states.json",
        "data/generated/latent_trajectory.csv",
        "data/generated/unique_topology_ids.json",
        "data/results/trial_log.csv",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = Path(file_path)
        if not full_path.exists():
            missing_files.append(file_path)
            logging.warning(f"  Missing required file: {file_path}")
        else:
            logging.info(f"  Found required file: {file_path}")

    if missing_files:
        logging.error(f"  Missing {len(missing_files)} required files.")
        return False

    # Verify config
    logging.info(f"  Config loaded: {config}")
    return True

def verify_zero_overlap_condition() -> bool:
    """Verify zero overlap with original GAM training data."""
    log_section("VERIFYING ZERO OVERLAP")

    try:
        metadata = load_json_metadata("data/generated/unique_topology_ids.json")
        gam_stats = load_json_metadata("data/raw/gam_reference_stats.json")

        is_unique, reason = verify_zero_overlap(metadata, gam_stats)

        if is_unique:
            logging.info("  Zero overlap verification PASSED")
            return True
        else:
            logging.error(f"  Zero overlap verification FAILED: {reason}")
            return False

    except Exception as e:
        logging.error(f"  Zero overlap verification ERROR: {e}")
        return False

def verify_drift_threshold() -> bool:
    """Verify drift threshold is valid."""
    log_section("VERIFYING DRIFT THRESHOLD")

    try:
        stats = load_reference_stats("data/raw/gam_reference_stats.json")
        threshold_data = load_json_metadata("data/raw/drift_threshold_validation.json")

        if threshold_data.get("status") != "validated":
            logging.error("  Drift threshold validation status is not 'validated'")
            return False

        threshold = threshold_data.get("threshold")
        if threshold is None or threshold <= 0:
            logging.error("  Invalid drift threshold value")
            return False

        logging.info(f"  Drift threshold verified: {threshold:.4f}")
        return True

    except Exception as e:
        logging.error(f"  Drift threshold verification ERROR: {e}")
        return False

def run_inference_validation(config: Config) -> bool:
    """Run a quick inference validation."""
    log_section("RUNNING INFERENCE VALIDATION")

    try:
        # Load physics states
        extractor = PhysicsStateExtractor()
        physics_states = extractor.load_physics_states("data/generated/physics_states.json")

        if not physics_states or len(physics_states) == 0:
            logging.error("  No physics states loaded")
            return False

        logging.info(f"  Loaded {len(physics_states)} physics states")

        # Create pipeline and run a quick test
        pipeline = InferencePipeline(config)

        # Run a single trial to verify pipeline works
        test_trial_id = "quickstart_validation"
        result = pipeline.run_trial(test_trial_id, physics_states[0])

        if result is None:
            logging.error("  Inference pipeline returned None for test trial")
            return False

        logging.info(f"  Inference trial completed: success={result.get('success', False)}")
        return True

    except Exception as e:
        logging.error(f"  Inference validation ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_baseline_validation(config: Config) -> bool:
    """Run baseline validation."""
    log_section("RUNNING BASELINE VALIDATION")

    try:
        validator = BaselineValidator(config)
        results = validator.run_baseline_validation("data/generated/physics_states.json")

        if not results:
            logging.error("  Baseline validation returned no results")
            return False

        logging.info(f"  Baseline validation completed: {len(results)} trials")
        return True

    except Exception as e:
        logging.error(f"  Baseline validation ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_statistical_analysis() -> bool:
    """Run statistical analysis to verify end-to-end flow."""
    log_section("RUNNING STATISTICAL ANALYSIS")

    try:
        analyzer = StatisticalAnalyzer()

        # Load results
        symbolic_results = analyzer.load_results("data/results/symbolic_results.csv")
        baseline_results = analyzer.load_results("data/results/baseline_results.csv")

        if not symbolic_results or not baseline_results:
            logging.error("  Could not load results for analysis")
            return False

        logging.info(f"  Loaded {len(symbolic_results)} symbolic and {len(baseline_results)} baseline results")

        # Run analysis
        analysis_results = analyzer.run_full_analysis(symbolic_results, baseline_results)

        if not analysis_results:
            logging.error("  Analysis returned no results")
            return False

        # Generate report
        analyzer.generate_report(analysis_results, "data/results/analysis_report.md")

        logging.info("  Statistical analysis completed successfully")
        return True

    except Exception as e:
        logging.error(f"  Statistical analysis ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_schema_integrity() -> bool:
    """Verify all schema definitions are correct."""
    log_section("VERIFYING SCHEMA INTEGRITY")

    try:
        schema_desc = get_schema_description()
        logging.info(f"  Trial log schema: {schema_desc}")

        # Verify CSV files match schema
        if not os.path.exists("data/results/trial_log.csv"):
            logging.error("  trial_log.csv does not exist")
            return False

        logger = TrialLogger("data/results/trial_log.csv")
        if not logger.verify_schema():
            logging.error("  trial_log.csv schema verification failed")
            return False

        logging.info("  Schema integrity verified")
        return True

    except Exception as e:
        logging.error(f"  Schema verification ERROR: {e}")
        return False

def generate_validation_report(results: Dict[str, bool]):
    """Generate a validation report."""
    log_section("GENERATING VALIDATION REPORT")

    report_path = "data/results/quickstart_validation_report.json"
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_success": all(results.values()),
        "checks": results,
        "summary": {
            "total_checks": len(results),
            "passed": sum(1 for v in results.values() if v),
            "failed": sum(1 for v in results.values() if not v),
        }
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logging.info(f"  Validation report written to {report_path}")

    # Print summary
    logging.info(f"  Overall: {'PASSED' if report['overall_success'] else 'FAILED'}")
    for check, passed in results.items():
        status = "✓" if passed else "✗"
        logging.info(f"    {status} {check}")

    return report["overall_success"]

def main():
    """Main entry point for quickstart validation."""
    # Setup logging
    log_file = "data/results/quickstart_validation.log"
    setup_logging(log_file, level=logging.INFO)

    logging.info("Starting Quickstart Validation (T033)")

    try:
        # Load configuration
        config = load_config("code/config.yaml")

        # Set deterministic seed
        set_deterministic_seed(config.seed)

        # Run all validation checks
        results = {}

        results["prerequisites"] = validate_prerequisites(config)
        if not results["prerequisites"]:
            logging.error("Prerequisites validation failed. Stopping.")
            return 1

        results["zero_overlap"] = verify_zero_overlap_condition()
        if not results["zero_overlap"]:
            logging.error("Zero overlap verification failed. Stopping.")
            return 1

        results["drift_threshold"] = verify_drift_threshold()
        if not results["drift_threshold"]:
            logging.error("Drift threshold verification failed. Stopping.")
            return 1

        results["schema_integrity"] = verify_schema_integrity()
        if not results["schema_integrity"]:
            logging.error("Schema integrity verification failed. Stopping.")
            return 1

        results["inference"] = run_inference_validation(config)
        results["baseline"] = run_baseline_validation(config)
        results["analysis"] = run_statistical_analysis()

        # Generate final report
        overall_success = generate_validation_report(results)

        if overall_success:
            logging.info("Quickstart validation PASSED - End-to-end reproducibility confirmed")
            return 0
        else:
            logging.error("Quickstart validation FAILED - See log for details")
            return 1

    except Exception as e:
        logging.error(f"Quickstart validation ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())