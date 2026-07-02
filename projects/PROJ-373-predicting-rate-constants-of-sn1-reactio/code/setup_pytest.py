"""
Script to verify pytest installation and configuration.
Can be run to ensure the test environment is ready.
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("Verifying pytest installation...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Pytest version: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("ERROR: pytest is not installed or not in PATH.")
        print("Please install it via: pip install pytest jsonschema")
        return 1

    # Verify schema dependencies
    try:
        import jsonschema
        import yaml
        print("Dependencies (jsonschema, pyyaml) found.")
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        return 1

    # Check schema files exist
    schema_dir = Path("specs/001-predict-sn1-rate-constants/contracts")
    if not schema_dir.exists():
        print(f"ERROR: Schema directory not found at {schema_dir}")
        return 1

    schemas = ["dataset.schema.yaml", "model_output.schema.yaml", "exclusion_report.schema.yaml"]
    for s in schemas:
        if not (schema_dir / s).exists():
            print(f"ERROR: Missing schema file: {schema_dir / s}")
            return 1

    print("All checks passed. Run 'pytest' to execute tests.")
    return 0

if __name__ == "__main__":
    sys.exit(main())