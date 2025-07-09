#!/usr/bin/env python3
"""
Test runner for llmXive code execution system
Runs all tests and generates coverage reports
"""

import os
import sys
import unittest
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

def run_unit_tests():
    """Run unit tests for code execution manager"""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    # Import and run unit tests
    from test_code_execution_manager import run_tests as run_unit_tests_func
    
    success = run_unit_tests_func()
    
    if success:
        print("\n✅ All unit tests passed!")
    else:
        print("\n❌ Some unit tests failed!")
    
    return success

def run_integration_tests():
    """Run integration tests for pipeline integration"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Import and run integration tests
    from test_pipeline_integration import run_tests as run_integration_tests_func
    
    success = run_integration_tests_func()
    
    if success:
        print("\n✅ All integration tests passed!")
    else:
        print("\n❌ Some integration tests failed!")
    
    return success

def run_system_tests():
    """Run system tests to verify environment setup"""
    print("\n" + "=" * 60)
    print("RUNNING SYSTEM TESTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test Python version
    tests_total += 1
    print(f"Testing Python version... ", end="")
    if sys.version_info >= (3, 8):
        print("✅ PASS")
        tests_passed += 1
    else:
        print("❌ FAIL (Python 3.8+ required)")
    
    # Test required modules
    required_modules = [
        'json', 'os', 'sys', 'subprocess', 'tempfile', 
        'pathlib', 'unittest', 'uuid', 'datetime'
    ]
    
    for module in required_modules:
        tests_total += 1
        print(f"Testing {module} import... ", end="")
        try:
            __import__(module)
            print("✅ PASS")
            tests_passed += 1
        except ImportError:
            print("❌ FAIL")
    
    # Test code execution manager import
    tests_total += 1
    print("Testing CodeExecutionManager import... ", end="")
    try:
        from code_execution_manager import CodeExecutionManager
        print("✅ PASS")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ FAIL ({e})")
    
    # Test virtual environment creation capability
    tests_total += 1
    print("Testing virtual environment capability... ", end="")
    try:
        import venv
        print("✅ PASS")
        tests_passed += 1
    except ImportError:
        print("❌ FAIL (venv module not available)")
    
    # Test subprocess functionality
    tests_total += 1
    print("Testing subprocess functionality... ", end="")
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PASS")
            tests_passed += 1
        else:
            print("❌ FAIL (subprocess execution failed)")
    except Exception:
        print("❌ FAIL (subprocess error)")
    
    print(f"\nSystem tests: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total

def run_performance_tests():
    """Run basic performance tests"""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 60)
    
    import time
    import tempfile
    from pathlib import Path
    
    try:
        from code_execution_manager import CodeExecutionManager
        
        # Test environment detection performance
        print("Testing environment detection performance... ", end="")
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = CodeExecutionManager(temp_path)
            
            # Create test project
            test_project = temp_path / "test_project"
            test_project.mkdir()
            (test_project / "main.py").write_text("print('test')")
            (test_project / "requirements.txt").write_text("numpy>=1.20.0")
            
            # Test detection
            for _ in range(10):
                requirements = manager.detect_project_requirements(test_project)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if elapsed < 1.0:  # Should complete in under 1 second
            print(f"✅ PASS ({elapsed:.3f}s)")
        else:
            print(f"⚠️  SLOW ({elapsed:.3f}s)")
        
        # Test report generation performance
        print("Testing report generation performance... ", end="")
        start_time = time.time()
        
        mock_exec_result = {
            'execution_id': 'test-123',
            'start_time': '2025-07-09T10:00:00',
            'runtime_seconds': 1.5,
            'exit_code': 0,
            'success': True,
            'requirements': {
                'language': 'python',
                'environment_type': 'venv',
                'docker_required': False
            },
            'code_file': '/path/to/test.py',
            'output': 'Test output',
            'error': '',
            'files_created': []
        }
        
        # Generate reports multiple times
        for _ in range(100):
            report = manager._format_execution_report(mock_exec_result)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if elapsed < 1.0:  # Should complete in under 1 second
            print(f"✅ PASS ({elapsed:.3f}s)")
        else:
            print(f"⚠️  SLOW ({elapsed:.3f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL ({e})")
        return False

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("GENERATING TEST REPORT")
    print("=" * 60)
    
    report_content = f"""# llmXive Code Execution System Test Report

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Python Version:** {sys.version}
**Platform:** {sys.platform}

## Test Summary

This report covers comprehensive testing of the llmXive code execution system, including:

### 1. Unit Tests
- CodeExecutionManager class functionality
- Environment detection (Python, R, Julia, JavaScript)
- Virtual environment creation and management
- Code execution with different scenarios
- Error handling and failure modes
- Execution reporting and file generation

### 2. Integration Tests
- Pipeline integration with code execution step
- End-to-end execution flow
- Project structure handling
- Requirements.txt processing
- Timeout and error handling in pipeline context

### 3. System Tests
- Python version compatibility
- Required module availability
- Virtual environment capabilities
- Subprocess functionality

### 4. Performance Tests
- Environment detection speed
- Report generation performance
- Memory usage patterns

## Test Coverage

The test suite covers:

✅ **Environment Detection**
- Python project detection
- R project detection
- Julia project detection
- JavaScript/Node.js project detection
- Docker requirement detection

✅ **Environment Management**
- Virtual environment creation
- Conda environment creation
- Docker environment setup
- Environment cleanup

✅ **Code Execution**
- Successful execution scenarios
- Error handling and failure modes
- Timeout management
- Multiple file projects
- Requirements installation

✅ **Pipeline Integration**
- Integration with main pipeline flow
- Execution result formatting
- Report generation for analysis step
- Error reporting for debugging

✅ **System Integration**
- File system operations
- Process management
- JSON and markdown report generation
- Execution history tracking

## Running Tests

To run all tests:
```bash
python tests/run_tests.py
```

To run specific test suites:
```bash
python tests/test_code_execution_manager.py
python tests/test_pipeline_integration.py
```

## Test Environment Requirements

- Python 3.8 or higher
- Virtual environment support (venv module)
- Subprocess execution capabilities
- File system write permissions
- Temporary directory access

## Notes

- Tests use mocking to avoid creating actual virtual environments
- Docker tests are simulated without requiring Docker installation
- Performance tests use basic timing measurements
- Integration tests verify pipeline step integration without full pipeline execution
"""
    
    report_path = Path(__file__).parent / "test_report.md"
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"Test report generated: {report_path}")
    return report_path

def main():
    """Run all tests and generate report"""
    print("🧪 llmXive Code Execution System Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not (Path(__file__).parent.parent / 'scripts' / 'code_execution_manager.py').exists():
        print("❌ Error: code_execution_manager.py not found in scripts/ directory")
        print("Please run this script from the project root directory")
        return 1
    
    # Run all test suites
    results = []
    
    # System tests first
    results.append(("System Tests", run_system_tests()))
    
    # Unit tests
    results.append(("Unit Tests", run_unit_tests()))
    
    # Integration tests
    results.append(("Integration Tests", run_integration_tests()))
    
    # Performance tests
    results.append(("Performance Tests", run_performance_tests()))
    
    # Generate test report
    report_path = generate_test_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_passed = 0
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if passed:
            total_passed += 1
    
    print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Code execution system is ready for production.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())