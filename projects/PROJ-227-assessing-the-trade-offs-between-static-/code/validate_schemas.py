"""
Script to validate JSON Schemas against sample data.
Used to verify T005 implementation.
"""
import sys
import yaml
import json
import jsonschema
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def generate_minimal_sample(schema_name: str) -> dict:
    """Generate minimal valid sample data for each schema."""
    samples = {
        "dataset.schema.yaml": {
            "dataset_id": "test-dataset",
            "language": "python",
            "source_url": "https://example.com",
            "download_timestamp": "2023-01-01T00:00:00Z",
            "record_count": 1,
            "checksum": "0" * 64,
            "samples": [{"task_id": "test-1", "code": "pass"}]
        },
        "analysis_log.schema.yaml": {
            "analysis_id": "test-analysis",
            "dataset_id": "test-dataset",
            "language": "python",
            "tool": "test-tool",
            "timestamp": "2023-01-01T00:00:00Z",
            "results": [{"snippet_id": "test-1", "status": "passed"}]
        },
        "analysis_results.schema.yaml": {
            "snippet_id": "test-1",
            "dataset_id": "test-dataset",
            "language": "python",
            "static_analysis": {
                "tool": "test-tool",
                "issue_count": 0,
                "issues": []
            },
            "dynamic_analysis": {
                "status": "passed"
            }
        },
        "dataset_manifest.schema.yaml": {
            "manifest_version": "1.0",
            "created_at": "2023-01-01T00:00:00Z",
            "datasets": [{
                "dataset_id": "test-dataset",
                "file_path": "data/raw/test.json",
                "record_count": 1,
                "language": "python",
                "static_only": False,
                "checksum": "0" * 64
            }],
            "summary": {
                "total_records": 1,
                "total_datasets": 1,
                "language_breakdown": {"python": 1, "javascript": 0, "java": 0},
                "static_only_count": 0,
                "dynamic_capable_count": 1
            },
            "validation_status": {"passed": True, "errors": [], "warnings": []}
        },
        "statistical_report.schema.yaml": {
            "report_id": "test-report",
            "generated_at": "2023-01-01T00:00:00Z",
            "methodology": {
                "primary_metric_static": "issue_detection_rate",
                "primary_metric_dynamic": "pass_rate",
                "correlation_method": "spearman",
                "significance_level": 0.05,
                "bonferroni_corrected": False,
                "deviations": []
            },
            "metrics": {
                "issue_detection_rate": {"overall": 0.5, "by_language": {"python": 0.5, "javascript": 0.0, "java": 0.0}},
                "pass_rate": {"overall": 0.8, "by_language": {"python": 0.8, "javascript": 0.0, "java": 0.0}}
            },
            "correlation_results": {
                "spearman": {"coefficient": 0.0, "p_value": 1.0, "sample_size": 1},
                "chi_squared": {"statistic": 0.0, "p_value": 1.0, "degrees_of_freedom": 1}
            },
            "stratified_results": [],
            "sensitivity_analysis": [],
            "limitations": [],
            "artifacts": {}
        },
        "tool_version.schema.yaml": {
            "recorded_at": "2023-01-01T00:00:00Z",
            "tools": [{
                "name": "test-tool",
                "version": "1.0.0",
                "path_or_id": "/usr/bin/test",
                "platform": "linux",
                "install_method": "system"
            }],
            "verification_status": {"all_verified": True, "failed_verifications": []}
        }
    }
    return samples.get(schema_name, {})

def main():
    """Validate all schemas against minimal sample data."""
    schema_files = [
        "dataset.schema.yaml",
        "analysis_log.schema.yaml",
        "analysis_results.schema.yaml",
        "dataset_manifest.schema.yaml",
        "statistical_report.schema.yaml",
        "tool_version.schema.yaml"
    ]

    all_valid = True

    for schema_file in schema_files:
        schema_path = CONTRACTS_DIR / schema_file
        if not schema_path.exists():
            print(f"ERROR: Schema file missing: {schema_path}")
            all_valid = False
            continue

        try:
            # Load schema
            schema = load_schema(schema_path)
            print(f"✓ Loaded schema: {schema_file}")

            # Generate sample
            sample = generate_minimal_sample(schema_file)

            # Validate
            jsonschema.validate(instance=sample, schema=schema)
            print(f"✓ Validated sample against: {schema_file}")

        except yaml.YAMLError as e:
            print(f"ERROR: Invalid YAML in {schema_file}: {e}")
            all_valid = False
        except jsonschema.ValidationError as e:
            print(f"ERROR: Validation failed for {schema_file}: {e.message}")
            all_valid = False
        except Exception as e:
            print(f"ERROR: Unexpected error for {schema_file}: {e}")
            all_valid = False

    if all_valid:
        print("\n✓ All schemas are valid and successfully validated sample data.")
        return 0
    else:
        print("\n✗ Some schemas failed validation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())