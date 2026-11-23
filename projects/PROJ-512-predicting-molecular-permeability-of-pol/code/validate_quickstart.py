"""
Quickstart validation script for PROJ-512.
Verifies the execution of the pipeline steps and production of required artifacts.
"""
import os
import sys
import logging
import json
import time
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EVAL_RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"

# Required artifacts
REQUIRED_ARTIFACTS = {
    "polymers.h5": DATA_PROCESSED_DIR / "polymers.h5",
    "metrics.json": EVAL_RESULTS_DIR / "metrics.json",
    "sensitivity_sweep.json": EVAL_RESULTS_DIR / "sensitivity_sweep.json",
}

# Scripts to run (in order)
PIPELINE_STEPS = [
    {
        "name": "Data Ingestion",
        "script": "main.py",
        "args": ["--step", "ingestion"],
        "description": "Fetch data and generate simulation if needed."
    },
    {
        "name": "Preprocessing",
        "script": "main.py",
        "args": ["--step", "preprocessing"],
        "description": "Extract features and split data."
    },
    {
        "name": "Model Training",
        "script": "main.py",
        "args": ["--step", "training"],
        "description": "Train GNN and baselines."
    },
    {
        "name": "Evaluation & Stats",
        "script": "main.py",
        "args": ["--step", "evaluation"],
        "description": "Compute metrics and statistical validation."
    },
]

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure basic logging for the validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_file_exists(path: Path, step_name: str) -> bool:
    """Check if a required file exists."""
    if not path.exists():
        logger.error(f"❌ MISSING: {path} (Expected after {step_name})")
        return False
    logger.info(f"✅ FOUND: {path}")
    return True

def run_step(step: dict) -> bool:
    """Run a specific pipeline step via main.py."""
    logger.info(f"🚀 Running: {step['name']}")
    logger.info(f"   Command: python {step['script']} {' '.join(step['args'])}")

    # Import and run the main logic directly to avoid shell subprocess issues
    # We assume main.py has a function `main` that accepts args or parses sys.argv
    # Since we can't easily pass args to a module import without sys.argv manipulation,
    # we will simulate the step execution by calling the specific functions
    # defined in the API surface, assuming they are wired up in main.py.

    # To be robust, we will attempt to import the main function and pass the args
    # or manipulate sys.argv temporarily.
    original_argv = sys.argv
    try:
        sys.argv = [step['script']] + step['args']
        
        # We need to import main from the code directory
        # Add code dir to path if not already there
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        
        # Import the main module
        # Note: This assumes the script is run from the project root or code dir
        # If running from code dir, 'main' is the module.
        # We need to be careful about imports.
        
        # Let's try to import the specific module functions based on the step
        # This is a bit of a hack, but safer than shelling out if environment is strict.
        # However, the task asks to "Run quickstart.md validation".
        # The safest way to "run" is to execute the logic.
        
        # Let's assume main.py has a dispatcher.
        # We will try to import and run the main function.
        # Since the API surface shows `from main import main`, we can do:
        
        # We need to ensure we are importing from the correct location.
        # If we are in code/, `import main` works.
        
        # Reset sys.path to ensure we pick up local modules
        if str(PROJECT_ROOT / "code") not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT / "code"))
        
        # Force reload if already imported (in case of previous runs in same session)
        if 'main' in sys.modules:
            del sys.modules['main']
        
        import main as main_module
        
        # The main function in main.py likely parses sys.argv.
        # We have already set sys.argv.
        main_module.main()
        
        logger.info(f"✅ SUCCESS: {step['name']} completed without error.")
        return True

    except Exception as e:
        logger.error(f"❌ FAILED: {step['name']} raised {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        sys.argv = original_argv

def main():
    """Main validation routine."""
    setup_logging()
    
    logger.info("🔍 Starting Quickstart Validation for PROJ-512")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    
    # 1. Check initial state (optional, but good for logging)
    logger.info("📂 Checking directory structure...")
    if not DATA_RAW_DIR.exists():
        logger.warning(f"⚠️ Directory not found: {DATA_RAW_DIR}")
    if not DATA_PROCESSED_DIR.exists():
        logger.warning(f"⚠️ Directory not found: {DATA_PROCESSED_DIR}")
    if not EVAL_RESULTS_DIR.exists():
        logger.warning(f"⚠️ Directory not found: {EVAL_RESULTS_DIR}")

    # 2. Run pipeline steps
    all_steps_passed = True
    for step in PIPELINE_STEPS:
        if not run_step(step):
            all_steps_passed = False
            # Depending on strictness, we might stop here or continue to see other errors
            # For validation, let's stop at first major failure to save time
            break
        
        # Small delay to ensure file writes are flushed
        time.sleep(0.5)

    if not all_steps_passed:
        logger.error("❌ Pipeline execution failed. Validation aborted.")
        sys.exit(1)

    # 3. Verify artifacts
    logger.info("\n📦 Verifying required artifacts...")
    artifacts_ok = True
    for name, path in REQUIRED_ARTIFACTS.items():
        if not check_file_exists(path, "Pipeline Execution"):
            artifacts_ok = False

    if not artifacts_ok:
        logger.error("❌ Required artifacts are missing.")
        sys.exit(1)

    # 4. Validate artifact contents (basic check)
    logger.info("\n🔎 Validating artifact contents...")
    
    # Check polymers.h5 is not empty
    if REQUIRED_ARTIFACTS["polymers.h5"].stat().st_size == 0:
        logger.error("❌ polymers.h5 is empty.")
        sys.exit(1)
    
    # Check JSON files are valid JSON
    for name in ["metrics.json", "sensitivity_sweep.json"]:
        path = REQUIRED_ARTIFACTS[name]
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"⚠️ {name} is valid JSON but not a dict.")
            else:
                logger.info(f"✅ {name} is valid JSON with {len(data)} keys.")
        except json.JSONDecodeError as e:
            logger.error(f"❌ {name} is not valid JSON: {e}")
            sys.exit(1)

    logger.info("\n🎉 Quickstart Validation PASSED successfully!")
    logger.info("All required artifacts (polymers.h5, metrics.json, sensitivity_sweep.json) produced.")
    return 0

if __name__ == "__main__":
    sys.exit(main())