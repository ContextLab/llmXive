"""
Quickstart Validation Script for PROJ-244
Validates full pipeline execution within the 4-hour wall-clock budget.
Executes all phases sequentially and measures total runtime.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
WALL_CLOCK_LIMIT_SECONDS = 4 * 3600  # 4 hours
PHASES = [
    ('Phase 0', 'research.sample_size_estimator'),
    ('Phase 0', 'research.power_analysis'),
    ('Phase 0', 'research.cpu_feasibility'),
    ('Phase 3', 'ingestion.preprocess'),
    ('Phase 4', 'modeling.ml_models'),
    ('Phase 4', 'modeling.empirical_models'),
    ('Phase 4', 'modeling.evaluation'),
    ('Phase 4', 'modeling.sensitivity_analysis'),
    ('Phase 5', 'modeling.evaluation'),
    ('Phase 5', 'visualization.plots'),
    ('Phase 5', 'visualization.failure_regimes'),
    ('Phase 6', 'reporting.compile_metrics'),
    ('Phase 6', 'reporting.append_failure_regimes'),
]

def run_phase(phase_name: str, module_name: str) -> bool:
    """Run a specific phase module and return success status."""
    logger.info(f"Starting {phase_name}: {module_name}")
    start_time = time.time()
    
    try:
        # Import the module
        module = __import__(module_name, fromlist=['main'])
        
        # Check if main function exists
        if not hasattr(module, 'main'):
            logger.warning(f"{module_name} has no main function, skipping execution")
            return True
        
        # Run the main function
        module.main()
        
        elapsed = time.time() - start_time
        logger.info(f"Completed {phase_name}: {module_name} in {elapsed:.2f}s")
        return True
        
    except Exception as e:
        logger.error(f"Failed {phase_name}: {module_name} - {str(e)}")
        return False

def validate_outputs() -> bool:
    """Validate that all expected output files exist."""
    logger.info("Validating output artifacts...")
    required_outputs = [
        'data/processed/encoded_features.csv',
        'data/processed/train.csv',
        'data/processed/test.csv',
        'data/models/ml_rf.pkl',
        'data/models/empirical_params.yaml',
        'data/processed/cv_scores.csv',
        'results/robustness_metrics.json',
        'data/processed/shap_values.csv',
        'results/feature_importance_report.json',
        'results/plots/pdp_summary.png',
        'data/processed/failure_regimes.csv',
        'data/processed/metrics.json',
        'data/processed/wilcoxon_test.csv',
    ]
    
    all_exist = True
    for output_path in required_outputs:
        full_path = project_root / output_path
        if not full_path.exists():
            logger.error(f"Missing required output: {output_path}")
            all_exist = False
        else:
            logger.info(f"Found output: {output_path}")
    
    return all_exist

def main():
    """Main validation entry point."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation Pipeline")
    logger.info(f"Wall-clock limit: {WALL_CLOCK_LIMIT_SECONDS / 3600:.1f} hours")
    logger.info("=" * 60)
    
    total_start = time.time()
    phase_results = {}
    
    # Execute all phases
    for phase_name, module_name in PHASES:
        success = run_phase(phase_name, module_name)
        phase_results[module_name] = success
        
        # Check wall-clock limit after each phase
        elapsed_total = time.time() - total_start
        if elapsed_total > WALL_CLOCK_LIMIT_SECONDS:
            logger.error(f"Wall-clock limit exceeded! Total time: {elapsed_total:.2f}s")
            break
    
    total_elapsed = time.time() - total_start
    total_hours = total_elapsed / 3600
    
    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total execution time: {total_elapsed:.2f}s ({total_hours:.2f} hours)")
    logger.info(f"Wall-clock limit: {WALL_CLOCK_LIMIT_SECONDS}s ({WALL_CLOCK_LIMIT_SECONDS/3600:.2f} hours)")
    
    passed_phases = sum(1 for v in phase_results.values() if v)
    total_phases = len(phase_results)
    logger.info(f"Phases passed: {passed_phases}/{total_phases}")
    
    # Validate outputs
    outputs_valid = validate_outputs()
    
    # Final verdict
    success = (total_elapsed <= WALL_CLOCK_LIMIT_SECONDS) and outputs_valid and (passed_phases == total_phases)
    
    if success:
        logger.info("✅ VALIDATION PASSED: Pipeline completed within 4-hour limit")
    else:
        logger.error("❌ VALIDATION FAILED")
        if total_elapsed > WALL_CLOCK_LIMIT_SECONDS:
            logger.error("Reason: Exceeded 4-hour wall-clock limit")
        if not outputs_valid:
            logger.error("Reason: Missing required output artifacts")
        if passed_phases < total_phases:
            logger.error("Reason: Some phases failed to execute")
    
    # Save validation report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_time_seconds': total_elapsed,
        'time_limit_seconds': WALL_CLOCK_LIMIT_SECONDS,
        'passed_phases': passed_phases,
        'total_phases': total_phases,
        'outputs_valid': outputs_valid,
        'success': success,
        'phase_results': phase_results
    }
    
    report_path = project_root / 'results' / 'quickstart_validation_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to: {report_path}")
    logger.info("=" * 60)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())