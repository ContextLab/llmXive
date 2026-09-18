import sys
import yaml
import jsonschema
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file and return it as a dictionary."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_minimal_sample(schema: dict) -> dict:
    """
    Generate a minimal valid sample data object based on the schema.
    This is used for testing schema validation.
    """
    # Hardcoded minimal samples for each known schema to ensure validity
    # without complex recursive generation logic.
    schema_title = schema.get('title', '')
    
    if 'Dataset Schema' in schema_title:
        return {
            "id": "test-001",
            "source": "human-eval",
            "language": "python",
            "code": "def add(a, b):\n    return a + b",
            "prompt": "Add two numbers",
            "test": "assert add(1, 2) == 3",
            "stratum": "python",
            "static_only": False
        }
    elif 'Analysis Log Schema' in schema_title:
        return {
            "log_id": "log-001",
            "timestamp": "2023-10-27T10:00:00Z",
            "tool_name": "codeql",
            "tool_version": "2.13.0",
            "dataset_id": "test-001",
            "status": "success",
            "issues": [],
            "duration_seconds": 1.5
        }
    elif 'Analysis Results Schema' in schema_title:
        return {
            "dataset_id": "test-001",
            "static_issues_count": 0,
            "dynamic_pass": True,
            "static_tool_used": "codeql",
            "dynamic_tool_used": "pytest"
        }
    elif 'Dataset Manifest Schema' in schema_title:
        return {
            "manifest_version": "1.0",
            "generated_at": "2023-10-27T10:00:00Z",
            "total_records": 1,
            "records": [
                {
                    "id": "test-001",
                    "source": "human-eval",
                    "language": "python",
                    "stratum": "python",
                    "static_only": False,
                    "file_path": "data/raw/test-001.json"
                }
            ]
        }
    elif 'Statistical Report Schema' in schema_title:
        return {
            "report_id": "report-001",
            "generated_at": "2023-10-27T10:00:00Z",
            "metrics": {
                "issue_detection_rate": 0.5,
                "pass_rate": 0.8,
                "precision": "N/A",
                "recall": "N/A",
                "f1_score": "N/A"
            },
            "correlations": {
                "spearman": {
                    "coefficient": 0.2,
                    "p_value": 0.03
                },
                "chi_squared": {
                    "statistic": 5.0,
                    "p_value": 0.02,
                    "degrees_of_freedom": 1
                },
                "mcnemar": "N/A"
            },
            "stratified_results": {},
            "sensitivity_analysis": {
                "alpha_0_01": {},
                "alpha_0_05": {},
                "alpha_0_1": {}
            },
            "deviation_notes": ["See SPEC_AMENDMENT_001"]
        }
    elif 'Tool Version Schema' in schema_title:
        return {
            "tool_name": "codeql",
            "version": "2.13.0",
            "installed_at": "2023-10-27T10:00:00Z",
            "path": "/usr/local/bin/codeql"
        }
    else:
        # Fallback for unknown schemas: return empty object if no required fields
        required = schema.get('required', [])
        if not required:
            return {}
        # If we don't know the schema but it has required fields, we can't safely generate
        # In a real scenario, we might raise an error, but for this task we assume known schemas.
        raise ValueError(f"Unknown schema title: {schema_title}")

def main():
    """
    Main function to validate all schemas against minimal samples.
    """
    base_dir = Path(__file__).parent.parent
    contracts_dir = base_dir / 'contracts'
    
    schema_files = [
        'dataset.schema.yaml',
        'analysis_log.schema.yaml',
        'analysis_results.schema.yaml',
        'dataset_manifest.schema.yaml',
        'statistical_report.schema.yaml',
        'tool_version.schema.yaml'
    ]
    
    all_valid = True
    
    for schema_file in schema_files:
        schema_path = contracts_dir / schema_file
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {schema_path}")
            all_valid = False
            continue
        
        try:
            schema = load_schema(str(schema_path))
            sample = generate_minimal_sample(schema)
            jsonschema.validate(instance=sample, schema=schema)
            print(f"OK: {schema_file} validated successfully.")
        except jsonschema.ValidationError as e:
            print(f"FAIL: {schema_file} validation error: {e.message}")
            all_valid = False
        except Exception as e:
            print(f"ERROR: {schema_file} processing error: {e}")
            all_valid = False
    
    if all_valid:
        print("\nAll schemas validated successfully.")
        sys.exit(0)
    else:
        print("\nSome schemas failed validation.")
        sys.exit(1)

if __name__ == '__main__':
    main()