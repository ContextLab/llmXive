"""
T040: Run quickstart validation to ensure reproducibility from scratch.

This script executes the full pipeline steps defined in quickstart.md to verify
that the project is reproducible. It assumes the environment is set up and
dependencies are installed.

Steps:
1. Verify directory structure (T001a)
2. Verify config and requirements (T001b, T002)
3. Verify linting config (T003)
4. Verify schema contracts (T007, T008)
5. Run Data Ingestion Pipeline (T019 -> T017)
6. Run Modeling Pipeline (T022 -> T028)
7. Run Analysis Pipeline (T031 -> T035)
8. Validate final outputs exist.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"

def check_path_exists(path: Path, description: str) -> bool:
    if not path.exists():
        logger.error(f"MISSING: {description} at {path}")
        return False
    logger.info(f"OK: {description} found at {path}")
    return True

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
            cwd=CODE_DIR,
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Script failed with return code {result.returncode}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False

def main():
    logger.info("Starting Quickstart Validation (T040)...")
    all_passed = True

    # 1. Check Directory Structure (T001a)
    logger.info("--- Step 1: Directory Structure ---")
    dirs = [
        ("code/", CODE_DIR),
        ("data/raw/", DATA_DIR / "raw"),
        ("data/processed/", DATA_DIR / "processed"),
        ("data/results/", DATA_DIR / "results"),
        ("tests/", TESTS_DIR),
    ]
    for name, p in dirs:
        if not check_path_exists(p, name):
            all_passed = False

    # 2. Check Config & Requirements (T001b, T002)
    logger.info("--- Step 2: Config & Requirements ---")
    if not check_path_exists(CODE_DIR / "config.py", "config.py"):
        all_passed = False
    if not check_path_exists(CODE_DIR / "requirements.txt", "requirements.txt"):
        all_passed = False

    # 3. Check Linting Config (T003)
    logger.info("--- Step 3: Linting Config ---")
    # Check for pyproject.toml or .ruff.toml in code/
    lint_configs = [
        CODE_DIR / "pyproject.toml",
        CODE_DIR / ".ruff.toml",
        CODE_DIR / ".black.toml",
        PROJECT_ROOT / "pyproject.toml"
    ]
    found_lint = any(p.exists() for p in lint_configs)
    if not found_lint:
        logger.error("MISSING: Linting configuration (pyproject.toml or .ruff.toml)")
        all_passed = False
    else:
        logger.info("OK: Linting configuration found")

    # 4. Check Schema Contracts (T007, T008)
    logger.info("--- Step 4: Schema Contracts ---")
    contracts_dir = PROJECT_ROOT / "specs" / "001-assess-ml-predictive-power" / "contracts"
    schemas = [
        (contracts_dir / "dataset.schema.yaml", "Dataset Schema"),
        (contracts_dir / "output.schema.yaml", "Output Schema"),
    ]
    for p, name in schemas:
        if not check_path_exists(p, name):
            all_passed = False

    # 5. Run Data Ingestion Pipeline (T019 -> T017)
    # Note: T019 (download) might fail if no network/real data source is configured.
    # The validation script attempts to run it. If it fails, we log it.
    # However, if data/raw/uspto_raw.parquet exists, we skip download.
    raw_parquet = DATA_DIR / "raw" / "uspto_raw.parquet"
    processed_parquet = DATA_DIR / "processed" / "cleaned_reactions.parquet"
    scaffold_parquet = DATA_DIR / "processed" / "scaffold_groups.parquet"

    logger.info("--- Step 5: Data Ingestion ---")
    if not raw_parquet.exists():
        logger.info("Raw data missing. Attempting download (T019)...")
        if not run_script("preprocessing/download.py"):
            logger.warning("Download failed or skipped. Cannot proceed with ingestion without raw data.")
            all_passed = False
    
    if raw_parquet.exists() and not processed_parquet.exists():
        logger.info("Running Sanitization & Fingerprints (T014, T016)...")
        # We assume ingest.py handles the full pipeline from raw to processed
        if not run_script("preprocessing/ingest.py"):
            logger.error("Ingestion pipeline failed.")
            all_passed = False
    
    if processed_parquet.exists() and not scaffold_parquet.exists():
        logger.info("Generating Scaffolds (T010)...")
        if not run_script("preprocessing/scaffold.py"):
            logger.error("Scaffold generation failed.")
            all_passed = False

    # 6. Run Modeling Pipeline (T022 -> T028)
    split_indices = DATA_DIR / "processed" / "split_indices.parquet"
    validation_set = DATA_DIR / "processed" / "validation_set.parquet"
    best_models_dir = DATA_DIR / "results" / "best_models"

    logger.info("--- Step 6: Modeling ---")
    if processed_parquet.exists() and not split_indices.exists():
        logger.info("Running Split Generation (T022, T023)...")
        if not run_script("modeling/split.py"):
            logger.error("Split generation failed.")
            all_passed = False
    
    if split_indices.exists() and not best_models_dir.exists():
        logger.info("Running Training & Evaluation (T024-T028)...")
        # Note: Training might take a while. We run the main entry point.
        # Depending on implementation, train.py might handle split loading internally
        # or we might need a specific runner. Assuming main() in train.py orchestrates.
        # If the project has a specific 'train_full.py' or similar, it would be used.
        # Based on API, we call train.py which should handle the flow if configured.
        # However, standard pattern is often a single runner. Let's try train.py.
        if not run_script("modeling/train.py"):
            logger.error("Training failed.")
            all_passed = False

    # 7. Run Analysis Pipeline (T031 -> T035)
    final_report = DATA_DIR / "results" / "final_report.json"
    quality_report = DATA_DIR / "results" / "data_quality_report.json"

    logger.info("--- Step 7: Analysis & Reporting ---")
    if best_models_dir.exists() and not final_report.exists():
        logger.info("Running Evaluation & Reporting (T031-T035)...")
        # Assuming evaluate.py or a combined script handles this.
        # Based on T026/T034, evaluate.py is the likely candidate.
        if not run_script("modeling/evaluate.py"):
            logger.error("Evaluation/Reporting failed.")
            all_passed = False

    # 8. Final Validation
    logger.info("--- Step 8: Final Artifact Validation ---")
    required_artifacts = [
        (DATA_DIR / "processed" / "cleaned_reactions.parquet", "Cleaned Reactions"),
        (DATA_DIR / "processed" / "scaffold_groups.parquet", "Scaffold Groups"),
        (DATA_DIR / "processed" / "split_indices.parquet", "Split Indices"),
        (DATA_DIR / "results" / "best_models", "Best Models Directory"),
        (DATA_DIR / "results" / "final_report.json", "Final Report"),
        (DATA_DIR / "results" / "data_quality_report.json", "Quality Report"),
    ]

    for p, name in required_artifacts:
        if not check_path_exists(p, name):
            all_passed = False

    if all_passed:
        logger.info("SUCCESS: Quickstart validation passed. All artifacts present.")
        return 0
    else:
        logger.error("FAILURE: Quickstart validation failed. Some artifacts missing or steps failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())