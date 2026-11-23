"""
Standalone runner for T020 Integration Test.
This file can be run directly to execute the full ingestion pipeline test
without relying on pytest discovery, useful for CI/CD or manual verification.
"""
import sys
import os
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

def run_integration_tests():
    """Run the integration test suite for T020."""
    from tests.test_ingestion import TestFullIngestionPipeline
    
    test_instance = TestFullIngestionPipeline()
    
    print("Running Setup...")
    test_instance.setup_method()
    
    try:
        print("Running test_full_pipeline_execution...")
        test_instance.test_full_pipeline_execution()
        
        print("Running test_pipeline_integration_with_main...")
        test_instance.test_pipeline_integration_with_main()
        
        print("\n=== ALL INTEGRATION TESTS PASSED ===")
        return True
    except Exception as e:
        print(f"\n=== INTEGRATION TEST FAILED ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        test_instance.teardown_method()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)