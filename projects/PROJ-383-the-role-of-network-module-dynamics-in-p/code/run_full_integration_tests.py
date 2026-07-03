"""
Script to run the full integration test suite for the pipeline.

This script executes all integration tests to verify the end-to-end pipeline
functionality. It is designed to be run after all individual components
have been implemented and tested.

Usage:
    python code/run_full_integration_tests.py
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests" / "integration"

def run_test_file(test_file: Path) -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file.name}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0

def main():
    """Run all integration tests."""
    print("🚀 Starting Full Integration Test Suite")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Tests Directory: {TESTS_DIR}")
    
    if not TESTS_DIR.exists():
        print(f"❌ Tests directory not found: {TESTS_DIR}")
        sys.exit(1)
    
    test_files = list(TESTS_DIR.glob("test_*.py"))
    
    if not test_files:
        print("❌ No test files found in integration directory")
        sys.exit(1)
    
    print(f"Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f.name}")
    
    results = {}
    for test_file in test_files:
        success = run_test_file(test_file)
        results[test_file.name] = success
    
    print(f"\n{'='*60}")
    print("Test Results Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        sys.exit(1)
    else:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()