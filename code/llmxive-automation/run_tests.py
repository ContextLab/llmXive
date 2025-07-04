#!/usr/bin/env python3
"""Test runner for llmXive automation tests"""

import sys
import subprocess
import argparse


def run_unit_tests():
    """Run unit tests only"""
    print("Running unit tests...")
    cmd = [
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing"
    ]
    return subprocess.run(cmd).returncode


def run_integration_tests():
    """Run integration tests (requires GPU)"""
    print("Running integration tests...")
    print("WARNING: This will download real models from HuggingFace!")
    
    cmd = [
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-s"  # Show output for debugging
    ]
    return subprocess.run(cmd).returncode


def run_specific_test(test_path):
    """Run a specific test file or test case"""
    print(f"Running specific test: {test_path}")
    cmd = ["pytest", test_path, "-v", "--tb=short"]
    return subprocess.run(cmd).returncode


def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    
    # First run unit tests
    unit_result = run_unit_tests()
    if unit_result != 0:
        print("\nUnit tests failed!")
        return unit_result
    
    # Then run integration tests if not in CI
    import os
    if os.environ.get('CI') != 'true':
        integration_result = run_integration_tests()
        if integration_result != 0:
            print("\nIntegration tests failed!")
            return integration_result
    else:
        print("\nSkipping integration tests in CI environment")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run llmXive automation tests")
    parser.add_argument(
        "--unit", 
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true", 
        help="Run integration tests only (requires GPU)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test file or test case"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke tests only"
    )
    
    args = parser.parse_args()
    
    # Default to unit tests if nothing specified
    if not any([args.unit, args.integration, args.all, args.test, args.quick]):
        args.unit = True
    
    if args.quick:
        # Run just a few key tests
        print("Running quick smoke tests...")
        cmd = [
            "pytest",
            "tests/unit/test_response_parser.py::TestResponseParser::test_parse_brainstorm_response",
            "tests/unit/test_task_executor.py::TestTaskExecutor::test_initialization",
            "-v"
        ]
        return subprocess.run(cmd).returncode
    
    if args.test:
        return run_specific_test(args.test)
    elif args.all:
        return run_all_tests()
    elif args.integration:
        return run_integration_tests()
    else:
        return run_unit_tests()


if __name__ == "__main__":
    sys.exit(main())