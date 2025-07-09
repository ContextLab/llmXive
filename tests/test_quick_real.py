#!/usr/bin/env python3
"""
Quick real integration tests for immediate verification
Tests core functionality without lengthy package installations
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


class TestQuickReal(unittest.TestCase):
    """Quick real tests to verify core functionality"""
    
    def setUp(self):
        """Set up test"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_quick_"))
        self.manager = CodeExecutionManager(self.temp_dir)
        print(f"\n🔧 Test directory: {self.temp_dir}")
        
    def tearDown(self):
        """Clean up"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"🧹 Cleaned up: {self.temp_dir}")
    
    def test_basic_python_execution(self):
        """Test basic Python execution without external packages"""
        print("\n🧪 Testing basic Python execution")
        
        # Create project
        project_path = self.temp_dir / "basic_test"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        
        # Simple script using only stdlib
        main_script = code_dir / "main.py"
        main_script.write_text("""#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

print("=== Basic Execution Test ===")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")

# Basic calculation
numbers = [1, 2, 3, 4, 5]
result = {
    "numbers": numbers,
    "sum": sum(numbers),
    "product": 1,
    "timestamp": datetime.now().isoformat()
}

for n in numbers:
    result["product"] *= n

print(f"Sum: {result['sum']}")
print(f"Product: {result['product']}")

# Save result
with open("basic_result.json", "w") as f:
    json.dump(result, f, indent=2)

print("=== Test Complete ===")
""")
        
        # Execute
        print("🚀 Executing basic Python script...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, main_script, timeout=120)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Completed in {elapsed:.2f} seconds")
        
        # Verify
        self.assertTrue(result['success'], f"Failed: {result['error']}")
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Basic Execution Test', result['output'])
        self.assertIn('Sum: 15', result['output'])
        self.assertIn('Product: 120', result['output'])
        
        # Check output file
        output_file = project_path / "basic_result.json"
        self.assertTrue(output_file.exists())
        
        with open(output_file) as f:
            data = json.load(f)
        self.assertEqual(data['sum'], 15)
        self.assertEqual(data['product'], 120)
        
        print("✅ Basic execution test passed")
    
    def test_environment_creation_directly(self):
        """Test that virtual environments are actually created"""
        print("\n🧪 Testing actual virtual environment creation")
        
        # Create project
        project_path = self.temp_dir / "venv_test"
        project_path.mkdir(parents=True)
        
        # Test environment detection
        requirements = self.manager.detect_project_requirements(project_path)
        print(f"Detected requirements: {requirements}")
        
        # Test environment creation
        print("🔨 Creating virtual environment...")
        start_time = time.time()
        
        env_path = self.manager.create_execution_environment(project_path, requirements)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Environment created in {elapsed:.2f} seconds")
        
        # Verify environment was actually created
        self.assertTrue(env_path.exists(), f"Environment path doesn't exist: {env_path}")
        
        # Check for venv structure
        if requirements['environment_type'] == 'venv':
            # Look for Python executable
            python_paths = [
                env_path / 'bin' / 'python',
                env_path / 'Scripts' / 'python.exe'  # Windows
            ]
            
            python_exists = any(p.exists() for p in python_paths)
            self.assertTrue(python_exists, f"Python executable not found in {env_path}")
            
            # Find the actual python path
            python_path = next((p for p in python_paths if p.exists()), None)
            if python_path:
                print(f"✅ Found Python executable: {python_path}")
                
                # Test that we can actually run Python in the environment
                result = subprocess.run([
                    str(python_path), '-c', 'import sys; print(f"Python {sys.version}")'
                ], capture_output=True, text=True, timeout=30)
                
                self.assertEqual(result.returncode, 0, f"Failed to run Python: {result.stderr}")
                self.assertIn('Python', result.stdout)
                print(f"✅ Environment Python working: {result.stdout.strip()}")
        
        print("✅ Environment creation test passed")
    
    def test_file_execution_in_environment(self):
        """Test executing a file in the created environment"""
        print("\n🧪 Testing file execution in real environment")
        
        # Create project
        project_path = self.temp_dir / "file_exec_test"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        
        # Create test script
        test_script = code_dir / "test.py"
        test_script.write_text("""#!/usr/bin/env python3
import sys
import os

print("Script executed successfully!")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print(f"Script path: {__file__}")

# Test that we can write files
with open("execution_proof.txt", "w") as f:
    f.write("This file proves the script executed\\n")
    f.write(f"Python version: {sys.version}\\n")

print("File created: execution_proof.txt")
""")
        
        # Execute using the manager
        print("🚀 Executing script in real environment...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, test_script, timeout=120)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Execution completed in {elapsed:.2f} seconds")
        
        # Verify execution
        self.assertTrue(result['success'], f"Execution failed: {result['error']}")
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Script executed successfully', result['output'])
        
        # Verify file was created
        proof_file = project_path / "execution_proof.txt"
        self.assertTrue(proof_file.exists(), "Proof file was not created")
        
        proof_content = proof_file.read_text()
        self.assertIn('This file proves the script executed', proof_content)
        self.assertIn('Python version:', proof_content)
        
        print("✅ File execution test passed")
    
    def test_error_capture(self):
        """Test that errors are properly captured"""
        print("\n🧪 Testing real error capture")
        
        # Create project
        project_path = self.temp_dir / "error_test"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        
        # Create script with error
        error_script = code_dir / "error.py"
        error_script.write_text("""#!/usr/bin/env python3
print("Starting script...")
print("About to cause an error...")

# This will cause an error
x = 1 / 0
print("This should not print")
""")
        
        # Execute
        print("🚀 Executing script with error...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, error_script, timeout=60)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Execution completed in {elapsed:.2f} seconds")
        
        # Verify error was captured
        self.assertFalse(result['success'], "Expected execution to fail")
        self.assertNotEqual(result['exit_code'], 0)
        self.assertIn('ZeroDivisionError', result['error'])
        
        # Verify we got partial output
        self.assertIn('Starting script', result['output'])
        self.assertIn('About to cause an error', result['output'])
        self.assertNotIn('This should not print', result['output'])
        
        print("✅ Error capture test passed")


def main():
    """Run quick real tests"""
    print("🚀 Quick Real Integration Tests")
    print("=" * 50)
    print("Testing actual environment creation and code execution")
    print("=" * 50)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestQuickReal)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n" + "=" * 50)
        print("🎉 ALL QUICK REAL TESTS PASSED!")
        print("✅ Core functionality verified")
        print("=" * 50)
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ SOME TESTS FAILED!")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())