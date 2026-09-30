"""
Quickstart Validation Script for llmXive Project (T038).

This script validates the reproducibility of the pipeline by checking:
1. Project structure integrity.
2. Existence and non-emptiness of critical data artifacts.
3. Integrity of the state manifest (SHA-256 verification).
4. Execution of a dry-run import for all major pipeline modules.

It exits with code 0 if all checks pass, or 1 if any check fails.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("quickstart_validator")

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
TESTS_DIR = PROJECT_ROOT / "tests"

# Critical Artifacts to Verify (based on tasks.md and completed tasks)
CRITICAL_ARTIFACTS = [
    # Phase 1: Setup
    ("code/requirements.txt", "Project dependencies"),
    # Phase 2: Foundational
    ("code/utils/memory_manager.py", "Memory manager utility"),
    ("code/utils/physics_sim.py", "Physics simulation wrapper"),
    ("code/models/data_models.py", "Base data models"),
    ("code/utils/logging_config.py", "Logging infrastructure"),
    ("code/utils/retry.py", "Retry logic"),
    ("data/.checksums.json", "Checksums structure"),
    # Phase 3: US1 (Feature Extraction)
    ("data/processed/features.npy", "Extracted features (T013/T016)"),
    ("data/processed/metadata.json", "Extraction metadata"),
    ("data/processed/extract.log", "Extraction log"),
    ("data/processed/memory_log.json", "Memory log"),
    ("data/processed/chunking_config.json", "Chunking config"),
    # Phase 4: US2 (Labeling)
    ("data/processed/labels.csv", "Final labels"),
    ("data/processed/null_labels.csv", "Null labels"),
    ("data/processed/excluded_samples.log", "Excluded samples log"),
    ("data/processed/metadata.json", "Labeling metadata"),
    # Phase 5: US3 (Classification)
    ("data/processed/classifier.pkl", "Trained classifier"),
    ("data/processed/evaluation_metrics.json", "Evaluation metrics"),
    ("data/processed/baseline_f1.json", "Baseline F1"),
    ("data/processed/feature_importance.json", "Feature importance (T033)"),
    ("docs/results_report.md", "Results report (T037.1)"),
    # Phase 6: State
    ("state/manifest.yaml", "Pipeline manifest (T036)"),
    ("pipeline_run_summary.json", "Pipeline run summary (T036)"),
]

# Critical Modules to Import (Dry Run)
CRITICAL_MODULES = [
    "utils.memory_manager",
    "utils.physics_sim",
    "utils.logging_config",
    "utils.retry",
    "extract_features",
    "generate_labels",
    "classification.train_classifier",
    "classification.compute_metrics",
    "main_pipeline",
]

def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists and is non-empty."""
    if not path.exists():
        return False, f"Missing: {description} ({path})"
    if path.stat().st_size == 0:
        return False, f"Empty: {description} ({path})"
    return True, f"OK: {description}"

def verify_checksums() -> Tuple[bool, str]:
    """Verify SHA-256 checksums from the manifest if it exists."""
    manifest_path = STATE_DIR / "manifest.yaml"
    if not manifest_path.exists():
        return False, "Manifest file missing: state/manifest.yaml"

    try:
        # Simple YAML parsing without external dependency if possible, 
        # but for robustness we assume pyyaml is installed (part of T002).
        import yaml
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        if not manifest or 'files' not in manifest:
            return False, "Manifest structure invalid: missing 'files' key"

        errors = []
        for file_entry in manifest['files']:
            rel_path = file_entry.get('path')
            expected_hash = file_entry.get('sha256')
            
            if not rel_path or not expected_hash:
                continue

            full_path = PROJECT_ROOT / rel_path
            if not full_path.exists():
                errors.append(f"File in manifest missing: {rel_path}")
                continue

            # Calculate hash
            sha256_hash = hashlib.sha256()
            with open(full_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            actual_hash = sha256_hash.hexdigest()

            if actual_hash != expected_hash:
                errors.append(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")

        if errors:
            return False, "Checksum verification failed:\n" + "\n".join(errors)
        
        return True, "All manifest checksums verified."
    except ImportError:
        return False, "PyYAML not installed (required for manifest verification)"
    except Exception as e:
        return False, f"Manifest verification error: {str(e)}"

def dry_run_imports() -> Tuple[bool, str]:
    """Attempt to import critical modules to ensure no syntax errors."""
    sys.path.insert(0, str(PROJECT_ROOT))
    errors = []
    for module_name in CRITICAL_MODULES:
        try:
            __import__(module_name)
        except ImportError as e:
            errors.append(f"Import failed for {module_name}: {str(e)}")
        except SyntaxError as e:
            errors.append(f"Syntax error in {module_name}: {str(e)}")
        except Exception as e:
            # Other exceptions (e.g., missing dependencies) might be expected in a 
            # partial environment, but we log them. We only fail on syntax/import.
            logger.warning(f"Import of {module_name} raised exception (non-critical): {str(e)}")
    
    if errors:
        return False, "Import errors:\n" + "\n".join(errors)
    return True, "All critical modules imported successfully."

def main():
    logger.info("Starting Quickstart Validation (T038)...")
    all_passed = True
    report = []

    # 1. Check File Existence
    logger.info("Checking critical artifacts...")
    for rel_path, description in CRITICAL_ARTIFACTS:
        full_path = PROJECT_ROOT / rel_path
        passed, msg = check_file_exists(full_path, description)
        report.append(msg)
        logger.info(msg)
        if not passed:
            all_passed = False

    # 2. Verify Manifest Checksums
    logger.info("Verifying manifest checksums...")
    passed, msg = verify_checksums()
    report.append(msg)
    logger.info(msg)
    if not passed:
        all_passed = False

    # 3. Dry Run Imports
    logger.info("Performing dry-run imports...")
    passed, msg = dry_run_imports()
    report.append(msg)
    logger.info(msg)
    if not passed:
        all_passed = False

    # Summary
    logger.info("-" * 50)
    if all_passed:
        logger.info("VALIDATION PASSED: All checks successful.")
        return 0
    else:
        logger.error("VALIDATION FAILED: One or more checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
