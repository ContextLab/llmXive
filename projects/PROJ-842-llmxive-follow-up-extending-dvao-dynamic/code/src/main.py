"""
Main entry point for the llmXive experiment suite.
Orchestrates the full integration test:
1. Derivation Verification (US1)
2. Environment Simulation & Data Generation (US2)
3. Statistical Analysis & Reporting (US3)
"""
import argparse
import os
import sys
import json
import logging
import traceback
from datetime import datetime

# Import components based on API surface
from src.environment.runner import main as run_environment_main
from src.derivation.symbolic_verification import main as run_symbolic_verification
from src.derivation.sample_complexity import main as run_sample_complexity
from scripts.run_heavy_tailed_validation import main as run_heavy_tailed_validation
from src.analysis.stats import main as run_stats_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration_suite.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        'logs', 'data/raw', 'data/processed', 'state',
        'docs', 'results', 'figures'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def check_required_artifacts():
    """
    Verify that critical output artifacts from previous phases exist.
    This is a soft check to ensure the pipeline flow is correct.
    """
    required_files = [
        'data/processed/empirical_results.json',
        'data/processed/heavy_tailed_results.json',
        'data/processed/construct_validity_report.json',
        'data/processed/correlation_sweep_results.json'
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        logger.warning(f"Missing expected artifacts (will be generated in this run): {missing}")
        return False
    return True

def run_full_sweep(args):
    """Execute the full experiment suite."""
    logger.info("Starting Full Integration Test Suite...")
    logger.info(f"Configuration: N sweep={args.n_sweep}, k_sweep={args.k_sweep}, seeds={args.seeds}")

    try:
        # 1. Symbolic Verification (US1)
        logger.info("Phase 1: Symbolic Verification...")
        run_symbolic_verification()
        run_sample_complexity()
        if not os.path.exists('docs/theoretical_derivation.md'):
            raise FileNotFoundError("Derivation output missing after symbolic verification.")

        # 2. Heavy Tailed Validation (US2 - Specific)
        logger.info("Phase 2: Heavy-Tailed Validation...")
        run_heavy_tailed_validation()
        if not os.path.exists('data/processed/heavy_tailed_results.json'):
            raise FileNotFoundError("Heavy-tailed results missing.")

        # 3. Environment Simulation (US2 - Main)
        logger.info("Phase 3: Main Environment Simulation (N-sweep)...")
        # We pass args to the runner to control the sweep
        # The runner handles the N-sweep internally based on config or args
        run_environment_main()
        
        # 4. Data Flow Check (T061 requirement)
        if not os.path.exists('data/processed/empirical_results.json'):
            raise FileNotFoundError(
                "ERROR: Missing required artifact data/processed/empirical_results.json. "
                "Analysis cannot proceed."
            )
        logger.info("Data flow dependency check passed: empirical_results.json exists.")

        # 5. Statistical Analysis (US3)
        logger.info("Phase 4: Statistical Analysis & Reporting...")
        run_stats_analysis()
        
        # 6. Final Verification
        logger.info("Phase 5: Final Verification of Outputs...")
        expected_outputs = [
            'data/processed/statistical_report.json',
            'data/processed/empirical_results.json',
            'data/processed/heavy_tailed_results.json',
            'data/processed/construct_validity_report.json',
            'data/processed/correlation_sweep_results.json'
        ]
        
        all_present = True
        for path in expected_outputs:
            if os.path.exists(path):
                # Verify it's valid JSON
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    logger.info(f"  [OK] {path}")
                except json.JSONDecodeError:
                    logger.error(f"  [FAIL] {path} is not valid JSON")
                    all_present = False
            else:
                logger.error(f"  [MISSING] {path}")
                all_present = False

        if all_present:
            logger.info("SUCCESS: All expected artifacts generated and validated.")
            return 0
        else:
            logger.error("FAILURE: Some expected artifacts are missing or invalid.")
            return 1

    except Exception as e:
        logger.error(f"CRITICAL ERROR during integration suite: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

def main():
    parser = argparse.ArgumentParser(description="llmXive Full Integration Test Suite")
    parser.add_argument('--run-full-sweep', action='store_true', 
                        help='Execute the complete experiment suite')
    parser.add_argument('--n-sweep', type=str, default='5,10,20,50',
                        help='Comma-separated list of N values to sweep')
    parser.add_argument('--k-sweep', type=str, default='0.01,0.05,0.1',
                        help='Comma-separated list of k values')
    parser.add_argument('--seeds', type=str, default='42,123,456',
                        help='Comma-separated list of random seeds')
    
    args = parser.parse_args()

    if not args.run_full_sweep:
        print("Usage: python src/main.py --run-full-sweep")
        sys.exit(1)

    ensure_directories()
    
    # Parse sweep arguments
    args.n_sweep = [int(x) for x in args.n_sweep.split(',')]
    args.k_sweep = [float(x) for x in args.k_sweep.split(',')]
    args.seeds = [int(x) for x in args.seeds.split(',')]

    exit_code = run_full_sweep(args)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()