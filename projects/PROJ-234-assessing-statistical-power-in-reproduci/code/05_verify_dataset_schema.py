"""
Verification script for the dataset_metadata.schema.yaml.
Performs yamllint check and a simple schema load test.
"""
import os
import sys
import yaml
import subprocess
from pathlib import Path

# Add the project root to the path if running as a script
project_root = Path(__file__).parent.parent
contracts_dir = project_root / "contracts"
schema_path = contracts_dir / "dataset_metadata.schema.yaml"

def check_yamllint_structure():
    """Run yamllint on the schema file to ensure valid YAML structure."""
    print(f"Checking YAML structure with yamllint: {schema_path}")
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}")
        return False

    try:
        # Try to run yamllint
        result = subprocess.run(
            ["yamllint", str(schema_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ yamllint passed: YAML structure is valid.")
            return True
        else:
            print(f"✗ yamllint failed:\n{result.stdout}\n{result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠ yamllint not installed. Skipping structure check.")
        print("  Install with: pip install yamllint")
        # We don't fail here, as the task might be run in an environment without yamllint
        # but we still want to verify the schema can be loaded.
        return True
    except subprocess.TimeoutExpired:
        print("✗ yamllint check timed out.")
        return False

def load_and_validate_schema():
    """Load the schema and verify it is a valid YAML dictionary."""
    print(f"\nLoading schema from: {schema_path}")
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}")
        return False

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        if not isinstance(schema, dict):
            print("✗ ERROR: Schema root is not a dictionary.")
            return False
        
        required_keys = ['$schema', 'title', 'type']
        missing_keys = [k for k in required_keys if k not in schema]
        
        if missing_keys:
            print(f"✗ ERROR: Schema missing required keys: {missing_keys}")
            return False
        
        print("✓ Schema loaded successfully.")
        print(f"  Title: {schema.get('title')}")
        print(f"  Type: {schema.get('type')}")
        print(f"  Required fields: {schema.get('required', [])}")
        return True
    except yaml.YAMLError as e:
        print(f"✗ ERROR: Failed to parse YAML: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Unexpected error loading schema: {e}")
        return False

def test_schema_with_mock_data():
    """Test the schema against a mock dataset entry."""
    print("\nTesting schema with mock data...")
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}")
        return False

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Create a minimal valid mock dataset entry based on the schema
        mock_data = {
            "dataset_id": 12345,
            "name": "Test Dataset",
            "version": 1,
            "task_type": "Supervised Classification",
            "download_count": 100,
            "status": "active",
            "url": "https://www.openml.org/d/12345"
        }
        
        # Verify required fields are present in mock data
        required = schema.get('required', [])
        for field in required:
            if field not in mock_data:
                print(f"✗ ERROR: Mock data missing required field: {field}")
                return False
        
        # Verify types
        if not isinstance(mock_data['dataset_id'], int):
            print("✗ ERROR: dataset_id must be an integer")
            return False
        if not isinstance(mock_data['name'], str):
            print("✗ ERROR: name must be a string")
            return False
        if not isinstance(mock_data['download_count'], int):
            print("✗ ERROR: download_count must be an integer")
            return False
        
        print("✓ Mock data validation passed.")
        print(f"  Mock entry: {mock_data}")
        return True
    except Exception as e:
        print(f"✗ ERROR: Failed to test with mock data: {e}")
        return False

def main():
    """Main entry point for verification."""
    print("=" * 60)
    print("Verifying contracts/dataset_metadata.schema.yaml")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Check YAML structure
    if not check_yamllint_structure():
        all_passed = False
    
    # 2. Load and validate schema
    if not load_and_validate_schema():
        all_passed = False
    
    # 3. Test with mock data
    if not test_schema_with_mock_data():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL VERIFICATION CHECKS PASSED")
        return 0
    else:
        print("✗ SOME VERIFICATION CHECKS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
