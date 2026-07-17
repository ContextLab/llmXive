"""
Script to demonstrate schema validation as required by T007.
Validates sample JSON records against Dataset, Metric, and Analysis schemas.
Raises an error on mismatch.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from contracts.dataset_schema import DatasetValidator
from contracts.metric_schema import MetricValidator
from contracts.analysis_schema import AnalysisValidator
from pydantic import ValidationError


def generate_sample_dataset() -> str:
    return json.dumps({
        "dataset_id": "demo-ds-001",
        "name": "Demo Dataset",
        "created_at": datetime.utcnow().isoformat(),
        "clips": [
            {
                "clip_id": "demo-clip-001",
                "source_dataset": "DAVIS",
                "duration_seconds": 5.0,
                "frame_count": 150,
                "resolution": [480, 640],
                "fps": 30.0,
                "motion_magnitude": 0.12,
                "stratification_group": "low"
            }
        ],
        "total_clips": 1,
        "metadata": {"demo": True}
    })


def generate_sample_metrics() -> str:
    return json.dumps({
        "experiment_id": "demo-exp-001",
        "model_name": "baseline",
        "generated_at": datetime.utcnow().isoformat(),
        "records": [
            {
                "record_id": "demo-rec-001",
                "clip_id": "demo-clip-001",
                "metric_type": "ssim",
                "value": 0.92,
                "unit": "unitless",
                "metadata": {"frame_idx": 5}
            }
        ],
        "total_records": 1
    })


def generate_sample_analysis() -> str:
    return json.dumps({
        "report_id": "demo-analysis-001",
        "created_at": datetime.utcnow().isoformat(),
        "comparisons": [
            {
                "result_id": "demo-res-001",
                "analysis_type": "sensitivity",
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": {"cutoffs": [0.01, 0.05, 0.1]},
                "results": [
                    {
                        "test_name": "KS_Test",
                        "statistic": 0.05,
                        "p_value": 0.85,
                        "conclusion": "No significant difference"
                    }
                ],
                "summary": "Sensitivity analysis passed."
            }
        ],
        "total_comparisons": 1,
        "metadata": {"demo": True}
    })


def main():
    parser = argparse.ArgumentParser(description="Validate sample JSON records against schemas.")
    parser.add_argument("--strict", action="store_true", help="Fail on first error instead of continuing")
    args = parser.parse_args()

    print("=== T007 Schema Validation Demo ===")
    print("Validating sample JSON records against Dataset, Metric, and Analysis schemas.\n")

    errors = []

    # 1. Validate Dataset
    print("1. Validating Dataset Schema...")
    try:
        sample_ds = generate_sample_dataset()
        DatasetValidator.validate_from_json(sample_ds)
        print("   [PASS] Dataset schema validation successful.")
    except ValidationError as e:
        msg = f"   [FAIL] Dataset schema validation failed: {e}"
        print(msg)
        errors.append(msg)

    # 2. Validate Metrics
    print("2. Validating Metric Schema...")
    try:
        sample_metrics = generate_sample_metrics()
        MetricValidator.validate_from_json(sample_metrics)
        print("   [PASS] Metric schema validation successful.")
    except ValidationError as e:
        msg = f"   [FAIL] Metric schema validation failed: {e}"
        print(msg)
        errors.append(msg)

    # 3. Validate Analysis
    print("3. Validating Analysis Schema...")
    try:
        sample_analysis = generate_sample_analysis()
        AnalysisValidator.validate_from_json(sample_analysis)
        print("   [PASS] Analysis schema validation successful.")
    except ValidationError as e:
        msg = f"   [FAIL] Analysis schema validation failed: {e}"
        print(msg)
        errors.append(msg)

    # 4. Validate Mismatch (Negative Test)
    print("\n4. Testing Negative Case (Invalid JSON)...")
    try:
        invalid_json = json.dumps({
            "dataset_id": "bad-id",
            "name": "Bad",
            "created_at": datetime.utcnow().isoformat(),
            # Missing 'clips' and 'total_clips' to trigger validation error
            "total_clips": 0
        })
        DatasetValidator.validate_from_json(invalid_json)
        msg = "   [FAIL] Negative test failed: Expected ValidationError but none raised."
        print(msg)
        errors.append(msg)
    except ValidationError:
        print("   [PASS] Negative test successful: ValidationError raised as expected.")

    print("\n=== Summary ===")
    if errors:
        print(f"Validation completed with {len(errors)} error(s).")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("All schema validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()