"""
Script to verify source code completeness for PROJ-006-agriculture-optimization.
Checks for existence of all files listed in plan.md.
"""
import os
import sys
from pathlib import Path

REQUIRED_FILES = [
    "src/cli/validate.py",
    "src/cli/run_pipeline.py",
    "src/data/collectors/survey_collector.py",
    "src/data/collectors/remote_sensing_collector.py",
    "src/data/processing/spatial_join.py",
    "src/data/processing/feature_engineering.py",
    "src/data/generators/structural_validation_generator.py",
    "src/analysis/run_regression.py",
    "src/analysis/sensitivity_check.py",
    "src/services/report_generator.py",
    "src/utils/io_helpers.py",
    "src/utils/state_manager.py",
    "src/config/constants.py",
    "src/config/schemas.py",
    "contracts/dataset.schema.yaml",
    "contracts/output.schema.yaml",
    "tests/contract/test_dataset_schema.py",
    "tests/contract/test_regression_output.py",
    "tests/contract/test_sensitivity.py",
    "tests/integration/test_ingestion.py",
    "tests/integration/test_regression.py",
    "tests/integration/test_report.py",
    "tests/unit/test_feature_engineering.py",
    "tests/unit/test_run_regression.py",
    "tests/unit/test_sensitivity_check.py",
    "tests/unit/test_remote_sensing_collector.py",
    "tests/unit/test_spatial_join.py",
]

def main():
    project_root = Path(__file__).parent.parent
    missing = []
    
    for file_path in REQUIRED_FILES:
        full_path = project_root / file_path
        if not full_path.exists():
            missing.append(file_path)
        elif full_path.stat().st_size == 0:
            missing.append(f"{file_path} (empty)")
    
    if missing:
        print("ERROR: Missing or empty files:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print("SUCCESS: All required source files exist and are non-empty.")
        sys.exit(0)

if __name__ == "__main__":
    main()