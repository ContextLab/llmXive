import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define expected artifacts based on tasks.md deliverables
EXPECTED_ARTIFACTS = {
    # Phase 2: Foundational
    "data/pilot/calibration_report.json": "Calibration report from T031",
    "data/pilot/raw_pilot_data.csv": "Raw pilot data from T031b",
    "code/simulate/bkt_params.yaml": "Updated BKT params from T031",
    
    # Phase 3: User Story 1 (Explanations)
    "data/raw/assistments_data.csv": "ASSISTments dataset from T012",
    "data/raw/khan_source_status.json": "Khan source verification from T012c",
    "data/raw/khan_academy_data.csv": "Khan Academy dataset from T012b",
    "data/generated/explanation_neural.txt": "Neural explanation artifact",
    "data/generated/explanation_symbolic.txt": "Symbolic explanation artifact",
    "data/generated/explanation_neuro_symbolic.txt": "Neuro-symbolic explanation artifact",
    
    # Phase 4: User Story 2 (Simulation)
    "data/derived/simulation_logs.csv": "Simulation logs from T022",
    "data/derived/rt_distribution_validation.json": "RT distribution validation from T023",
    "code/simulate/simulation_config.yaml": "Simulation config from T021b",
    
    # Phase 5: User Story 3 (Analysis)
    "data/derived/real_student_data_validated.csv": "Real student data from T034a",
    "data/derived/combined_logs.csv": "Merged logs from T034",
    "data/derived/analysis_results.json": "Analysis results from T026/T027",
    "data/derived/results.md": "Results markdown from T029",
    "data/derived/rt_histogram_check.json": "Histogram check from T037b",
    
    # Phase N: Polish
    "docs/symbolic_vs_neural_boundaries.md": "Documentation from T041",
}

def check_file_exists(path_str: str) -> bool:
    """Check if a file exists at the given relative path."""
    full_path = PROJECT_ROOT / path_str
    exists = full_path.exists()
    if exists:
        size = full_path.stat().st_size
        logger.info(f"✓ Found: {path_str} ({size} bytes)")
    else:
        logger.error(f"✗ Missing: {path_str}")
    return exists

def run_module(module_path: str) -> bool:
    """Attempt to import a module to verify it compiles and initializes."""
    try:
        # Convert path to module name
        module_name = module_path.replace('/', '.').replace('\\', '.')
        if module_name.startswith('code.'):
            module_name = module_name[5:]  # Remove 'code.' prefix for import
        
        logger.info(f"Attempting to import module: {module_name}")
        __import__(module_name)
        logger.info(f"✓ Module imported successfully: {module_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Module import failed: {module_path} - {str(e)}")
        return False

def verify_artifacts() -> dict:
    """Verify all expected artifacts exist and modules are importable."""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(PROJECT_ROOT),
        "artifacts_checked": {},
        "modules_checked": {},
        "summary": {
            "total_artifacts": 0,
            "found_artifacts": 0,
            "total_modules": 0,
            "imported_modules": 0,
            "passed": True
        }
    }
    
    # Check all expected artifacts
    results["summary"]["total_artifacts"] = len(EXPECTED_ARTIFACTS)
    for path_str, description in EXPECTED_ARTIFACTS.items():
        exists = check_file_exists(path_str)
        results["artifacts_checked"][path_str] = {
            "exists": exists,
            "description": description
        }
        if exists:
            results["summary"]["found_artifacts"] += 1
        else:
            results["summary"]["passed"] = False
    
    # Check key modules for importability
    key_modules = [
        "code/simulate/calibration.py",
        "code/generate/explanation_generator.py",
        "code/simulate/run_simulation.py",
        "code/analyze/mixed_effects.py",
        "code/analyze/effect_sizes.py",
        "code/download/fetch_assistments.py",
        "code/generate/symbolic_explanation.py",
        "code/generate/neural_explanation.py",
        "code/generate/neuro_symbolic_explanation.py"
    ]
    
    results["summary"]["total_modules"] = len(key_modules)
    for module_path in key_modules:
        imported = run_module(module_path)
        results["modules_checked"][module_path] = imported
        if imported:
            results["summary"]["imported_modules"] += 1
        else:
            results["summary"]["passed"] = False
    
    return results

def main():
    """Main entry point for quickstart validation."""
    parser = argparse.ArgumentParser(description="Validate quickstart.md execution")
    parser.add_argument("--output", "-o", type=str, default="data/quickstart_validation_report.json",
                      help="Path to save validation report")
    args = parser.parse_args()
    
    logger.info("Starting quickstart validation...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    
    # Verify artifacts
    results = verify_artifacts()
    
    # Save report
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation report saved to: {output_path}")
    
    # Print summary
    summary = results["summary"]
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Artifacts: {summary['found_artifacts']}/{summary['total_artifacts']} found")
    logger.info(f"Modules: {summary['imported_modules']}/{summary['total_modules']} imported")
    logger.info(f"Overall Status: {'PASSED' if summary['passed'] else 'FAILED'}")
    logger.info("=" * 50)
    
    if not summary["passed"]:
        logger.error("Quickstart validation FAILED. Review the report for missing artifacts or import errors.")
        sys.exit(1)
    else:
        logger.info("Quickstart validation PASSED. All required artifacts and modules are present.")
        sys.exit(0)

if __name__ == "__main__":
    main()