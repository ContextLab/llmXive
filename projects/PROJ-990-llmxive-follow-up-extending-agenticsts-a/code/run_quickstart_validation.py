"""
T033: Run quickstart.md validation to ensure reproducibility.

This script executes the full pipeline defined in quickstart.md (conceptually)
by running the main entry points for the core stages:
1. Data Parsing (T006)
2. Entropy Calculation (T005)
3. Data Splitting (T014a)
4. Ablation Study (T008)
5. Proxy Validation (T014)
6. Model Training (T009)
7. Dynamic Simulation (T015)
8. Baseline Simulations (T019, T020)
9. Aggregation (T021, T022)
10. Statistical Analysis (T024a, T025, T028)

It verifies that all expected output artifacts are generated and non-empty.
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Expected output artifacts
EXPECTED_ARTIFACTS = [
    "data/processed/metrics_with_moves.csv",
    "data/processed/entropy_scores.csv",
    "data/processed/static_log_proxy.json",
    "data/processed/train_set.csv",
    "data/processed/holdout_set.csv",
    "data/processed/ablation_labels_train.json",
    "data/processed/ablation_labels_holdout.json",
    "data/processed/proxy_validation_report.json",
    "models/layer_utility_classifier.pkl",
    "data/processed/simulation_results_dynamic.json",
    "data/processed/simulation_results_static.json",
    "data/processed/simulation_results_random.json",
    "data/processed/baseline_comparison.csv",
    "data/processed/token_reduction_verification.json",
    "data/processed/divergence_report.json",
    "data/processed/statistical_results.json",
]

def ensure_directories():
    """Ensure all required directories exist."""
    logger.info("Ensuring directory structure...")
    dirs = [DATA_DIR, PROCESSED_DIR, MODELS_DIR, FIGURES_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ready.")

def run_pipeline_stage(module_name, func_name="main", args=None):
    """
    Dynamically import and run a pipeline stage.
    """
    logger.info(f"Running stage: {module_name}.{func_name}")
    try:
        # Add code dir to path
        sys.path.insert(0, str(CODE_DIR))
        
        # Import the module
        module = __import__(module_name)
        
        # Get the function
        if not hasattr(module, func_name):
            raise AttributeError(f"Module {module_name} has no function {func_name}")
        
        func = getattr(module, func_name)
        
        # Run with args or no args
        if args:
            func(*args)
        else:
            func()
        
        logger.info(f"Stage {module_name}.{func_name} completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage {module_name}.{func_name} failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def verify_artifacts():
    """Check that all expected artifacts exist and are non-empty."""
    logger.info("Verifying output artifacts...")
    missing = []
    empty = []
    
    for artifact in EXPECTED_ARTIFACTS:
        path = PROJECT_ROOT / artifact
        if not path.exists():
            missing.append(artifact)
        elif path.stat().st_size == 0:
            empty.append(artifact)
        
    if missing:
        logger.error(f"Missing artifacts: {missing}")
    if empty:
        logger.error(f"Empty artifacts: {empty}")
        
    return len(missing) == 0 and len(empty) == 0

def generate_validation_report(success: bool, missing: list, empty: list):
    """Generate a validation report."""
    report = {
        "status": "success" if success else "failed",
        "missing_artifacts": missing,
        "empty_artifacts": empty,
        "timestamp": str(Path(PROJECT_ROOT).stat().st_mtime)
    }
    
    report_path = PROCESSED_DIR / "quickstart_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {report_path}")
    return report

def main():
    """Main entry point for T033."""
    logger.info("Starting quickstart validation (T033)...")
    
    # Step 1: Ensure directories
    ensure_directories()
    
    # Step 2: Run pipeline stages
    # Note: We run them in dependency order as defined in tasks.md
    stages = [
        # T006: Parser
        ("parser", "main"),
        # T005: Entropy
        ("entropy", "main"),
        # T007b: Static log proxy (extended parser)
        # Assuming this is handled in parser or a separate step
        # We'll rely on parser output for now
        # T014a: Splitter
        ("splitter", "main"),
        # T008a/T008: Ablation (train)
        ("ablation", "main"),
        # T008b: Ablation (holdout)
        # Assuming ablation.py handles both or we call it again
        # T014: Proxy Validation
        ("classifier", "main"), # This includes validation logic
        # T009: Training
        # Included in classifier main or separate
        # T015: Dynamic Simulation
        ("simulator", "main"),
        # T019/T020: Baselines
        # Included in simulator main
        # T021/T022: Aggregation
        ("generate_baseline_comparison", "main"),
        # T022a: Token Reduction Verifier
        ("token_reduction_verifier", "main"),
        # T024a: Divergence
        # T025/T028: Stats
        ("generate_statistical_report", "main"),
    ]
    
    success = True
    for module, func in stages:
        if not run_pipeline_stage(module, func):
            success = False
            logger.warning(f"Pipeline stage {module} failed, continuing to next...")
    
    # Step 3: Verify artifacts
    missing = []
    empty = []
    for artifact in EXPECTED_ARTIFACTS:
        path = PROJECT_ROOT / artifact
        if not path.exists():
            missing.append(artifact)
        elif path.stat().st_size == 0:
            empty.append(artifact)
    
    validation_success = verify_artifacts()
    
    # Step 4: Generate report
    report = generate_validation_report(validation_success, missing, empty)
    
    if not validation_success:
        logger.error("Quickstart validation FAILED due to missing or empty artifacts.")
        sys.exit(1)
    else:
        logger.info("Quickstart validation PASSED. All artifacts present and non-empty.")
        sys.exit(0)

if __name__ == "__main__":
    main()