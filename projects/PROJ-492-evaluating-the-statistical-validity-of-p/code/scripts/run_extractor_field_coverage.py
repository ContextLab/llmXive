"""
Script to run the FR-002 field coverage verification test.

This script executes the integration test defined in 
tests/integration/test_extractor_field_coverage.py to verify that
extracted fields exist for > 95% of valid pages.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run the field coverage verification."""
    test_module_path = project_root / "tests" / "integration" / "test_extractor_field_coverage.py"
    
    if not test_module_path.exists():
        print(f"Error: Test file not found at {test_module_path}")
        return 2

    # Import and run the test
    try:
        from tests.integration.test_extractor_field_coverage import main as run_test
        exit_code = run_test()
        return exit_code
    except ImportError as e:
        print(f"Error importing test module: {e}")
        return 2
    except Exception as e:
        print(f"Error running test: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())