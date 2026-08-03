"""
Validate the project by executing the steps defined in docs/quickstart.md.

This script performs a full end-to-end validation of the research pipeline,
ensuring that all major components (setup, topology generation, simulation,
analysis) function correctly and produce the expected artifacts.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Expected artifacts from the pipeline
EXPECTED_ARTIFACTS = [
    "data/processed/config.json",
    "data/processed/graph_metadata.json",
    "data/processed/simulation_results.csv",
    "data/processed/invariance_verification.json",
    "data/processed/stability_results.json",
    "data/processed/sensitivity_analysis.json",
    "data/processed/correlation_results.json",
    "data/processed/plot_kc_vs_p.png",
    "data/processed/analysis_report.md",
]

def run_script(script_name: str, args: list = None) -> bool:
    """Run a Python script from the code directory."""
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=False,
            timeout=3600  # 1 hour timeout for long running tasks
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out: {script_name}")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def verify_artifacts() -> bool:
    """Verify that all expected artifacts exist."""
    logger.info("Verifying expected artifacts...")
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact
        if not full_path.exists():
            missing.append(artifact)
        else:
            # Check for non-empty files (except .json which might be valid but small)
            if full_path.suffix in ['.png', '.csv', '.md']:
                if full_path.stat().st_size == 0:
                    logger.warning(f"File exists but is empty: {artifact}")
                    missing.append(artifact)
            elif full_path.suffix == '.json':
                try:
                    with open(full_path, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in: {artifact}")
                    missing.append(artifact)

    if missing:
        logger.error(f"Missing or invalid artifacts: {missing}")
        return False

    logger.info("All expected artifacts verified.")
    return True

def main() -> int:
    """Main validation entry point."""
    logger.info("Starting quickstart validation...")

    # 1. Verify project structure
    if not (CODE_DIR.exists() and DATA_DIR.exists()):
        logger.error("Project structure incomplete. Missing code/ or data/ directories.")
        return 1

    # 2. Check if config exists (indicates previous run)
    config_path = PROCESSED_DIR / "config.json"
    if not config_path.exists():
        logger.warning("Configuration not found. Running feasibility study first.")
        if not run_script("feasibility_study.py"):
            logger.error("Feasibility study failed.")
            return 1

    # 3. Run topology generation if graphs are missing
    graph_files = list(PROCESSED_DIR.glob("topology_*.gpickle"))
    if not graph_files:
        logger.info("No topology graphs found. Running generation.")
        if not run_script("generate_topology.py"):
            logger.error("Topology generation failed.")
            return 1
    else:
        logger.info(f"Found {len(graph_files)} topology graphs.")

    # 4. Run simulation if results are missing
    sim_results = PROCESSED_DIR / "simulation_results.csv"
    if not sim_results.exists():
        logger.info("Simulation results missing. Running simulation batch.")
        if not run_script("simulate_kuramoto.py"):
            logger.error("Simulation batch failed.")
            return 1
    else:
        logger.info("Simulation results found.")

    # 5. Run invariance verification
    if not (PROCESSED_DIR / "invariance_verification.json").exists():
        logger.info("Invariance verification missing. Running check.")
        if not run_script("verify_invariance.py"):
            logger.error("Invariance verification failed.")
            return 1

    # 6. Run stability check
    if not (PROCESSED_DIR / "stability_results.json").exists():
        logger.info("Stability results missing. Running check.")
        if not run_script("check_stability.py"):
            logger.error("Stability check failed.")
            return 1

    # 7. Run sensitivity analysis
    if not (PROCESSED_DIR / "sensitivity_analysis.json").exists():
        logger.info("Sensitivity analysis missing. Running analysis.")
        if not run_script("sensitivity_analysis.py"):
            logger.error("Sensitivity analysis failed.")
            return 1

    # 8. Run correlation analysis and report generation
    if not (PROCESSED_DIR / "correlation_results.json").exists():
        logger.info("Correlation results missing. Running analysis.")
        if not run_script("analyze_results.py"):
            logger.error("Correlation analysis failed.")
            return 1

    # 9. Verify all artifacts
    if not verify_artifacts():
        logger.error("Artifact verification failed.")
        return 1

    logger.info("Quickstart validation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
