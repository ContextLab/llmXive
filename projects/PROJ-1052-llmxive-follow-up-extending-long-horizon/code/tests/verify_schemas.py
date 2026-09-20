"""
Verification script for T005: Data Schema Contracts.

This script:
1. Validates YAML syntax of schema files using yamllint
2. Validates sample JSON data against the schemas using jsonschema CLI
"""
import json
import sys
import os
import tempfile
from pathlib import Path
import subprocess

# Add parent directory to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

SCHEMAS_DIR = Path("specs/001-reward-fidelity-error-recovery/contracts")
EXECUTION_LOG_SCHEMA = SCHEMAS_DIR / "execution_log.schema.yaml"
ANALYSIS_RESULT_SCHEMA = SCHEMAS_DIR / "analysis_result.schema.yaml"

# Sample valid data for testing
SAMPLE_EXECUTION_LOG = {
    "task_id": "task_lweb_001",
    "success": True,
    "trajectory": [
        {
            "step_id": 0,
            "observation": "Initial state",
            "action": "move_forward",
            "reward": 0.5,
            "is_recovery_critical": False,
            "segment_id": "seg_001"
        },
        {
            "step_id": 1,
            "observation": "Mid state",
            "action": "turn_left",
            "reward": 0.0,
            "is_recovery_critical": True,
            "segment_id": "seg_002"
        }
    ],
    "reward_fidelity_level": "dense",
    "recovery_segment_id": "seg_002",
    "token_count": 1250,
    "timestamp": "2024-01-15T10:30:00Z",
    "error_type": None,
    "pruned_segments": []
}

SAMPLE_ANALYSIS_RESULT = {
    "analysis_id": "analysis_001",
    "timestamp": "2024-01-15T12:00:00Z",
    "method": "logistic_regression",
    "results": {
        "inflection_point": 0.3,
        "logistic_coefficients": {
            "intercept": -0.5,
            "fidelity_coefficient": 2.1,
            "density_coefficient": 0.8
        },
        "p_value": 0.003,
        "p_value_corrected": 0.009,
        "statistical_power": 0.85,
        "trend_significance": None,
        "success_rate_by_fidelity": {
            "dense": {
                "success_count": 45,
                "total_count": 50,
                "rate": 0.9
            },
            "binary": {
                "success_count": 30,
                "total_count": 50,
                "rate": 0.6
            }
        },
        "token_savings": {
            "binary": {
                "average_savings_percent": 40.5,
                "total_tokens_saved": 25000
            }
        },
        "warnings": [],
        "fallback_reason": None
    }
}

def run_yamllint(schema_path: Path) -> bool:
    """Run yamllint on a schema file."""
    try:
        result = subprocess.run(
            ["yamllint", "-d", "relaxed", str(schema_path)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"✓ yamllint passed for {schema_path.name}")
            return True
        else:
            print(f"✗ yamllint failed for {schema_path.name}:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print(f"⚠ yamllint not found, skipping validation for {schema_path.name}")
        # If yamllint is not installed, we assume the YAML is valid if we can load it
        try:
            import yaml
            with open(schema_path, 'r') as f:
                yaml.safe_load(f)
            print(f"  (Manual YAML load check passed)")
            return True
        except Exception as e:
            print(f"✗ Manual YAML load failed: {e}")
            return False

def validate_json_against_schema(json_data: dict, schema_path: Path, schema_name: str) -> bool:
    """Validate a JSON object against a JSON Schema."""
    try:
        import yaml
        from jsonschema import validate, ValidationError

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        validate(instance=json_data, schema=schema)
        print(f"✓ JSON validation passed for {schema_name}")
        return True

    except ImportError as e:
        print(f"✗ Missing dependency for JSON validation: {e}")
        return False
    except ValidationError as e:
        print(f"✗ JSON validation failed for {schema_name}:")
        print(f"  Error: {e.message}")
        print(f"  Path: {list(e.path)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during JSON validation for {schema_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("T005 Schema Contract Verification")
    print("=" * 60)

    all_passed = True

    # 1. Validate YAML syntax
    print("\n[1/4] Validating YAML syntax...")
    if not run_yamllint(EXECUTION_LOG_SCHEMA):
        all_passed = False
    if not run_yamllint(ANALYSIS_RESULT_SCHEMA):
        all_passed = False

    # 2. Validate execution log sample
    print("\n[2/4] Validating execution log sample...")
    if not validate_json_against_schema(
        SAMPLE_EXECUTION_LOG,
        EXECUTION_LOG_SCHEMA,
        "execution_log.schema.yaml"
    ):
        all_passed = False

    # 3. Validate analysis result sample
    print("\n[3/4] Validating analysis result sample...")
    if not validate_json_against_schema(
        SAMPLE_ANALYSIS_RESULT,
        ANALYSIS_RESULT_SCHEMA,
        "analysis_result.schema.yaml"
    ):
        all_passed = False

    # 4. Write sample files to disk for CLI tool testing (optional)
    print("\n[4/4] Creating sample files for CLI tool testing...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        exec_log_file = tmpdir_path / "sample_exec_log.json"
        with open(exec_log_file, 'w') as f:
            json.dump(SAMPLE_EXECUTION_LOG, f, indent=2)
        
        analysis_file = tmpdir_path / "sample_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(SAMPLE_ANALYSIS_RESULT, f, indent=2)

        # Try to run jsonschema CLI if available
        try:
            subprocess.run(
                ["jsonschema", "-i", str(exec_log_file), str(EXECUTION_LOG_SCHEMA)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✓ jsonschema CLI validation passed for execution log")
        except FileNotFoundError:
            print("⚠ jsonschema CLI not found, skipping CLI validation")
        except subprocess.CalledProcessError as e:
            print(f"✗ jsonschema CLI validation failed: {e.stderr}")
            all_passed = False

        try:
            subprocess.run(
                ["jsonschema", "-i", str(analysis_file), str(ANALYSIS_RESULT_SCHEMA)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✓ jsonschema CLI validation passed for analysis result")
        except FileNotFoundError:
            print("⚠ jsonschema CLI not found, skipping CLI validation")
        except subprocess.CalledProcessError as e:
            print(f"✗ jsonschema CLI validation failed: {e.stderr}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All schema validations passed.")
        return 0
    else:
        print("FAILURE: One or more validations failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
