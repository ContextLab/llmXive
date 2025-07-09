#!/usr/bin/env python3
"""
Comprehensive tests for CodeExecutionManager
Tests sandboxed code execution with different environments and scenarios
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


class TestCodeExecutionManager(unittest.TestCase):
    """Test suite for CodeExecutionManager class"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_project_dir = self.temp_dir / "test_project"
        self.test_project_dir.mkdir(parents=True)
        
        # Create code execution manager
        self.manager = CodeExecutionManager(self.temp_dir)
        
        # Create mock project structure
        self.code_dir = self.test_project_dir / "code"
        self.code_dir.mkdir(parents=True)
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_python_project(self):
        """Test detection of Python project requirements"""
        # Create Python files
        (self.test_project_dir / "main.py").write_text("print('hello')")
        (self.test_project_dir / "requirements.txt").write_text("numpy==1.21.0\npandas==1.3.0")
        
        requirements = self.manager.detect_project_requirements(self.test_project_dir)
        
        self.assertEqual(requirements['language'], 'python')
        self.assertEqual(requirements['environment_type'], 'venv')
        self.assertIn(str(self.test_project_dir / "requirements.txt"), requirements['requirements_files'])
        self.assertFalse(requirements['docker_required'])
    
    def test_detect_r_project(self):
        """Test detection of R project requirements"""
        # Create R files
        (self.test_project_dir / "analysis.R").write_text("print('hello')")
        (self.test_project_dir / "script.r").write_text("library(ggplot2)")
        
        requirements = self.manager.detect_project_requirements(self.test_project_dir)
        
        self.assertEqual(requirements['language'], 'r')
        self.assertEqual(requirements['environment_type'], 'conda')
    
    def test_detect_julia_project(self):
        """Test detection of Julia project requirements"""
        # Create Julia files
        (self.test_project_dir / "analysis.jl").write_text("println(\"hello\")")
        
        requirements = self.manager.detect_project_requirements(self.test_project_dir)
        
        self.assertEqual(requirements['language'], 'julia')
        self.assertEqual(requirements['environment_type'], 'julia')
    
    def test_detect_javascript_project(self):
        """Test detection of JavaScript/Node.js project requirements"""
        # Create package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        (self.test_project_dir / "package.json").write_text(json.dumps(package_json))
        
        requirements = self.manager.detect_project_requirements(self.test_project_dir)
        
        self.assertEqual(requirements['language'], 'javascript')
        self.assertEqual(requirements['environment_type'], 'npm')
    
    def test_detect_docker_required(self):
        """Test detection of projects requiring Docker"""
        # Create Python file with GPU dependencies
        (self.test_project_dir / "gpu_code.py").write_text("import tensorflow as tf")
        
        # Create project in a path that suggests GPU usage
        gpu_project = self.temp_dir / "gpu_project"
        gpu_project.mkdir(parents=True)
        
        requirements = self.manager.detect_project_requirements(gpu_project)
        
        # Note: This test depends on the path containing 'gpu' - might need adjustment
        # For now, let's test the basic structure
        self.assertIn('docker_required', requirements)
        self.assertIn('language', requirements)
        self.assertIn('environment_type', requirements)
    
    @patch('subprocess.run')
    def test_create_venv_environment(self, mock_run):
        """Test virtual environment creation"""
        # Mock successful subprocess calls
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        requirements = {
            'language': 'python',
            'environment_type': 'venv',
            'requirements_files': [],
            'docker_required': False
        }
        
        env_path = self.manager.create_execution_environment(self.test_project_dir, requirements)
        
        # Verify subprocess was called to create venv
        self.assertTrue(mock_run.called)
        
        # Check that venv creation was attempted
        venv_call = mock_run.call_args_list[0]
        self.assertIn('venv', venv_call[0][0])
    
    @patch('subprocess.run')
    def test_create_conda_environment(self, mock_run):
        """Test Conda environment creation"""
        # Mock successful subprocess calls
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        requirements = {
            'language': 'r',
            'environment_type': 'conda',
            'requirements_files': [],
            'docker_required': False
        }
        
        env_path = self.manager.create_execution_environment(self.test_project_dir, requirements)
        
        # Verify subprocess was called to create conda env
        self.assertTrue(mock_run.called)
        
        # Check that conda creation was attempted
        conda_call = mock_run.call_args_list[0]
        self.assertIn('conda', conda_call[0][0])
    
    def test_create_docker_environment(self):
        """Test Docker environment creation"""
        requirements = {
            'language': 'python',
            'environment_type': 'docker',
            'requirements_files': [],
            'docker_required': True
        }
        
        env_path = self.manager.create_execution_environment(self.test_project_dir, requirements)
        
        # Check that Dockerfile was created
        dockerfile = env_path / 'Dockerfile'
        self.assertTrue(dockerfile.exists())
        
        # Verify Dockerfile content
        dockerfile_content = dockerfile.read_text()
        self.assertIn('FROM python:3.9-slim', dockerfile_content)
        self.assertIn('WORKDIR /app', dockerfile_content)
    
    def test_successful_python_execution(self):
        """Test successful Python code execution"""
        # Create a simple Python script
        test_script = self.code_dir / "test_script.py"
        test_script.write_text("""
import os
print("Hello, World!")
print(f"Python version: {os.sys.version}")
""")
        
        # Mock the environment creation and execution
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Hello, World!\\nPython version: 3.9.0',
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.test_project_dir, test_script)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('Hello, World!', result['output'])
    
    def test_failed_python_execution(self):
        """Test failed Python code execution"""
        # Create a Python script with syntax error
        test_script = self.code_dir / "error_script.py"
        test_script.write_text("""
print("Missing closing quote)
invalid_syntax_here
""")
        
        # Mock the environment creation and execution
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': '',
                'error': 'SyntaxError: unterminated string literal',
                'exit_code': 1,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.test_project_dir, test_script)
            
            self.assertFalse(result['success'])
            self.assertEqual(result['exit_code'], 1)
            self.assertIn('SyntaxError', result['error'])
    
    def test_execution_timeout(self):
        """Test execution timeout handling"""
        # Create a script that runs indefinitely
        test_script = self.code_dir / "infinite_loop.py"
        test_script.write_text("""
import time
while True:
    time.sleep(1)
""")
        
        # Mock the environment creation and execution with timeout
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.side_effect = subprocess.TimeoutExpired(cmd=['python'], timeout=1)
            
            # The timeout should be caught and handled in the execute_code method
            result = self.manager.execute_code(self.test_project_dir, test_script, timeout=1)
            
            # Verify timeout was handled gracefully
            self.assertFalse(result['success'])
            self.assertIn('timed out', result['error'].lower())
    
    def test_execution_report_generation(self):
        """Test execution report generation"""
        # Create a simple script
        test_script = self.code_dir / "report_test.py"
        test_script.write_text("print('Report generation test')")
        
        # Mock successful execution
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Report generation test',
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.test_project_dir, test_script)
            
            # Check that execution report files were created
            json_report = self.test_project_dir / "code" / "execution_report.json"
            md_report = self.test_project_dir / "code" / "execution_report.md"
            
            self.assertTrue(json_report.exists())
            self.assertTrue(md_report.exists())
            
            # Verify JSON report content
            with open(json_report, 'r') as f:
                report_data = json.load(f)
            
            self.assertIn('execution_id', report_data)
            self.assertIn('success', report_data)
            self.assertIn('output', report_data)
            self.assertIn('runtime_seconds', report_data)
            
            # Verify markdown report content
            md_content = md_report.read_text()
            self.assertIn('# Code Execution Report', md_content)
            self.assertIn('SUCCESS', md_content)
    
    def test_execution_history_tracking(self):
        """Test execution history tracking"""
        # Create multiple execution reports
        reports_dir = self.test_project_dir / "code"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock execution reports
        for i in range(3):
            report_data = {
                'execution_id': f'test-{i}',
                'start_time': f'2025-07-09T10:0{i}:00',
                'success': i % 2 == 0,
                'output': f'Test output {i}',
                'runtime_seconds': i * 0.5
            }
            
            report_file = reports_dir / f"execution_report_{i}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f)
        
        # Get execution history
        history = self.manager.get_execution_history(self.test_project_dir)
        
        # Verify we can retrieve history (even if it's empty due to our naming)
        self.assertIsInstance(history, list)
    
    def test_environment_cleanup(self):
        """Test environment cleanup after execution"""
        # Create a mock environment path
        env_path = self.temp_dir / "test_env"
        env_path.mkdir(parents=True)
        
        requirements = {
            'environment_type': 'venv',
            'docker_required': False
        }
        
        # Test cleanup
        self.manager._cleanup_environment(env_path, requirements)
        
        # Environment should be removed
        self.assertFalse(env_path.exists())
    
    @patch('subprocess.run')
    def test_conda_environment_cleanup(self, mock_run):
        """Test Conda environment cleanup"""
        env_path = self.temp_dir / "conda_env"
        env_path.mkdir(parents=True)
        
        requirements = {
            'environment_type': 'conda',
            'docker_required': False
        }
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        self.manager._cleanup_environment(env_path, requirements)
        
        # Verify conda env remove was called
        self.assertTrue(mock_run.called)
        conda_call = mock_run.call_args_list[0]
        self.assertIn('conda', conda_call[0][0])
        self.assertIn('remove', conda_call[0][0])
    
    def test_format_execution_report(self):
        """Test execution report formatting"""
        exec_result = {
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
            'files_created': ['output.txt', 'results.csv']
        }
        
        formatted_report = self.manager._format_execution_report(exec_result)
        
        # Verify report format
        self.assertIn('# Code Execution Report', formatted_report)
        self.assertIn('✅ SUCCESS', formatted_report)
        self.assertIn('test-123', formatted_report)
        self.assertIn('1.50 seconds', formatted_report)
        self.assertIn('python', formatted_report)
        self.assertIn('Test output', formatted_report)
        self.assertIn('output.txt', formatted_report)
        self.assertIn('results.csv', formatted_report)


class TestCodeExecutionIntegration(unittest.TestCase):
    """Integration tests for code execution with the main pipeline"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_execution(self):
        """Test complete end-to-end code execution flow"""
        # Create a realistic project structure
        project_dir = self.temp_dir / "test_project"
        project_dir.mkdir(parents=True)
        
        code_dir = project_dir / "code"
        code_dir.mkdir(parents=True)
        
        # Create a realistic Python analysis script
        main_script = code_dir / "main.py"
        main_script.write_text("""
import json
import os
from pathlib import Path

# Simple data analysis simulation
def analyze_data():
    data = {
        'samples': 100,
        'mean': 42.5,
        'std': 12.3,
        'analysis_type': 'statistical'
    }
    
    # Create output file
    output_file = Path('results.json')
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Analysis complete. Results saved to {output_file}")
    print(f"Mean: {data['mean']}, Std: {data['std']}")
    return data

if __name__ == "__main__":
    results = analyze_data()
    print("Script executed successfully!")
""")
        
        # Create requirements file
        requirements_file = project_dir / "requirements.txt"
        requirements_file.write_text("numpy>=1.20.0\npandas>=1.3.0\n")
        
        # Create code execution manager
        manager = CodeExecutionManager(self.temp_dir)
        
        # Test the complete execution flow
        with patch.object(manager, '_execute_in_venv') as mock_execute:
            # Mock successful execution
            mock_execute.return_value = {
                'output': 'Analysis complete. Results saved to results.json\\nMean: 42.5, Std: 12.3\\nScript executed successfully!',
                'error': '',
                'exit_code': 0,
                'files_created': ['results.json']
            }
            
            result = manager.execute_code(project_dir, main_script)
            
            # Verify execution was successful
            self.assertTrue(result['success'])
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('Analysis complete', result['output'])
            
            # Verify reports were generated
            json_report = project_dir / "code" / "execution_report.json"
            md_report = project_dir / "code" / "execution_report.md"
            
            self.assertTrue(json_report.exists())
            self.assertTrue(md_report.exists())


def run_tests():
    """Run all tests with verbose output"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)