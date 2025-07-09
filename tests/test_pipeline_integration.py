#!/usr/bin/env python3
"""
Integration tests for llmXive pipeline with code execution
Tests the complete pipeline flow including code execution step
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

try:
    from code_execution_manager import CodeExecutionManager
    # Note: Can't import llmxive-cli directly due to dash in filename
    # We'll test the integration through direct method calls
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure scripts directory is in the Python path")
    sys.exit(1)


class TestPipelineIntegration(unittest.TestCase):
    """Test pipeline integration with code execution"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_id = "PROJ-TEST-001"
        self.project_path = self.temp_dir / self.project_id
        self.project_path.mkdir(parents=True)
        
        # Create project structure
        self.code_dir = self.project_path / "code"
        self.code_dir.mkdir(parents=True)
        
        # Create code execution manager
        self.manager = CodeExecutionManager(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_project_code_success(self):
        """Test successful project code execution"""
        # Create a main.py file
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
import json
import numpy as np

def main():
    data = {
        'project': 'test',
        'results': [1, 2, 3, 4, 5],
        'mean': 3.0,
        'status': 'success'
    }
    
    print("Analysis starting...")
    print(f"Processing {len(data['results'])} data points")
    print(f"Mean value: {data['mean']}")
    print("Analysis complete!")
    
    # Save results
    with open('output.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == "__main__":
    results = main()
    print(f"Final results: {results}")
""")
        
        # Mock the execution environment
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Analysis starting...\nProcessing 5 data points\nMean value: 3.0\nAnalysis complete!\nFinal results: {...}',
                'error': '',
                'exit_code': 0,
                'files_created': ['output.json']
            }
            
            result = self.manager.execute_code(self.project_path, main_file)
            
            # Verify successful execution
            self.assertTrue(result['success'])
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('Analysis starting', result['output'])
            self.assertIn('output.json', result['files_created'])
            
            # Verify execution report was created
            report_file = self.project_path / "code" / "execution_report.json"
            self.assertTrue(report_file.exists())
    
    def test_execute_project_code_failure(self):
        """Test project code execution with errors"""
        # Create a main.py file with errors
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
import non_existent_module  # This will cause ImportError
import json

def main():
    # This won't run due to import error
    print("This should not run")
    
if __name__ == "__main__":
    main()
""")
        
        # Mock the execution environment
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': '',
                'error': 'ImportError: No module named \'non_existent_module\'',
                'exit_code': 1,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.project_path, main_file)
            
            # Verify failed execution
            self.assertFalse(result['success'])
            self.assertEqual(result['exit_code'], 1)
            self.assertIn('ImportError', result['error'])
            
            # Verify execution report was created
            report_file = self.project_path / "code" / "execution_report.json"
            self.assertTrue(report_file.exists())
    
    def test_execute_project_code_no_main_file(self):
        """Test project code execution when no main file exists"""
        # Don't create any Python files
        
        # Mock the execution environment
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env:
            mock_create_env.return_value = self.temp_dir / "mock_env"
            
            # This should handle the missing file gracefully
            result = self.manager.execute_code(self.project_path, self.code_dir / "nonexistent.py")
            
            # Verify the error was handled
            self.assertFalse(result['success'])
            # The error should contain some indication of file not found
            self.assertTrue(
                'No such file' in result['error'] or 
                'not found' in result['error'] or
                'FileNotFoundError' in result['error']
            )
    
    def test_execute_project_code_with_multiple_files(self):
        """Test project code execution with multiple Python files"""
        # Create multiple Python files
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
from utils import calculate_stats

def main():
    data = [1, 2, 3, 4, 5]
    stats = calculate_stats(data)
    print(f"Statistics: {stats}")
    return stats

if __name__ == "__main__":
    results = main()
""")
        
        utils_file = self.code_dir / "utils.py"
        utils_file.write_text("""
def calculate_stats(data):
    return {
        'mean': sum(data) / len(data),
        'count': len(data),
        'min': min(data),
        'max': max(data)
    }
""")
        
        # Mock the execution environment
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': "Statistics: {'mean': 3.0, 'count': 5, 'min': 1, 'max': 5}",
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.project_path, main_file)
            
            # Verify successful execution
            self.assertTrue(result['success'])
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('Statistics:', result['output'])
    
    def test_execute_project_code_with_requirements(self):
        """Test project code execution with requirements.txt"""
        # Create requirements.txt
        requirements_file = self.project_path / "requirements.txt"
        requirements_file.write_text("numpy>=1.20.0\npandas>=1.3.0\nmatplotlib>=3.5.0\n")
        
        # Create main.py that uses these packages
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # Create sample data
    data = np.random.normal(0, 1, 1000)
    df = pd.DataFrame({'values': data})
    
    print(f"Data shape: {df.shape}")
    print(f"Mean: {df['values'].mean():.3f}")
    print(f"Std: {df['values'].std():.3f}")
    
    # Save plot
    plt.figure(figsize=(10, 6))
    plt.hist(df['values'], bins=50, alpha=0.7)
    plt.title('Data Distribution')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.savefig('distribution.png')
    plt.close()
    
    print("Plot saved as distribution.png")
    
    return df.describe()

if __name__ == "__main__":
    results = main()
    print("Analysis complete!")
""")
        
        # Mock the execution environment
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Data shape: (1000, 1)\nMean: -0.015\nStd: 0.998\nPlot saved as distribution.png\nAnalysis complete!',
                'error': '',
                'exit_code': 0,
                'files_created': ['distribution.png']
            }
            
            result = self.manager.execute_code(self.project_path, main_file)
            
            # Verify successful execution
            self.assertTrue(result['success'])
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('Data shape:', result['output'])
            self.assertIn('distribution.png', result['files_created'])
    
    def test_execution_with_timeout(self):
        """Test execution with timeout handling"""
        # Create a script that would run for a long time
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
import time

def main():
    print("Starting long operation...")
    time.sleep(10)  # Sleep for 10 seconds
    print("Operation complete!")

if __name__ == "__main__":
    main()
""")
        
        # Mock the execution environment with timeout
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            
            # Simulate timeout by raising TimeoutExpired
            import subprocess
            mock_execute.side_effect = subprocess.TimeoutExpired(cmd=['python'], timeout=5)
            
            # This should handle the timeout gracefully
            result = self.manager.execute_code(self.project_path, main_file, timeout=5)
            
            # Verify timeout was handled
            self.assertFalse(result['success'])
            # The error message contains "timed out" not "timeout"
            self.assertIn('timed out', result['error'].lower())
    
    def test_pipeline_execution_step_integration(self):
        """Test integration with pipeline execution step"""
        # Create a mock pipeline orchestrator method
        def mock_execute_project_code(project_id, project_path):
            """Mock implementation of execute_project_code method"""
            # Find main code file
            code_dir = project_path / 'code'
            main_file = code_dir / 'main.py'
            
            if not main_file.exists():
                raise FileNotFoundError("No executable code file found")
            
            # Execute the code
            exec_result = self.manager.execute_code(project_path, main_file)
            
            return exec_result
        
        # Create test project structure
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
print("Pipeline integration test")
result = {"status": "success", "data": [1, 2, 3]}
print(f"Result: {result}")
""")
        
        # Mock the execution
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Pipeline integration test\nResult: {\'status\': \'success\', \'data\': [1, 2, 3]}',
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            # Test the pipeline integration
            result = mock_execute_project_code(self.project_id, self.project_path)
            
            # Verify integration worked
            self.assertTrue(result['success'])
            self.assertIn('Pipeline integration test', result['output'])
    
    def test_execution_results_format(self):
        """Test execution results format for pipeline consumption"""
        # Create a simple test script
        main_file = self.code_dir / "main.py"
        main_file.write_text("""
import json

data = {
    "experiment": "test",
    "results": [10, 20, 30],
    "success": True
}

print(json.dumps(data, indent=2))
""")
        
        # Mock the execution
        with patch.object(self.manager, 'create_execution_environment') as mock_create_env, \
             patch.object(self.manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': '{\n  "experiment": "test",\n  "results": [10, 20, 30],\n  "success": true\n}',
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            result = self.manager.execute_code(self.project_path, main_file)
            
            # Verify the result has all expected fields for pipeline consumption
            expected_fields = [
                'execution_id', 'start_time', 'end_time', 'success', 
                'output', 'error', 'exit_code', 'runtime_seconds',
                'files_created', 'code_file', 'requirements'
            ]
            
            for field in expected_fields:
                self.assertIn(field, result, f"Missing field: {field}")
            
            # Verify execution report generation
            json_report = self.project_path / "code" / "execution_report.json"
            md_report = self.project_path / "code" / "execution_report.md"
            
            self.assertTrue(json_report.exists())
            self.assertTrue(md_report.exists())
            
            # Verify JSON report content
            with open(json_report, 'r') as f:
                report_data = json.load(f)
            
            for field in expected_fields:
                self.assertIn(field, report_data, f"Missing field in report: {field}")


class TestPipelineExecutionFlow(unittest.TestCase):
    """Test the complete pipeline execution flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_step_sequence(self):
        """Test the sequence of pipeline steps including code execution"""
        # Simulate the pipeline steps
        steps = [
            "idea_generation",
            "technical_design", 
            "implementation_plan",
            "code_generation",
            "code_execution",  # Our new step
            "data_analysis",
            "paper_writing"
        ]
        
        project_id = "TEST-PIPELINE-001"
        project_path = self.temp_dir / project_id
        
        # Create project structure
        for step in steps:
            step_dir = project_path / step.replace('_', '-')
            step_dir.mkdir(parents=True, exist_ok=True)
        
        # Create code for execution step
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        main_file = code_dir / "main.py"
        main_file.write_text("""
# Generated code for pipeline test
def analyze_data():
    results = {
        'step': 'code_execution',
        'status': 'success',
        'pipeline_integration': True
    }
    
    print("Code execution step completed")
    print(f"Results: {results}")
    return results

if __name__ == "__main__":
    results = analyze_data()
""")
        
        # Test execution step
        manager = CodeExecutionManager(self.temp_dir)
        
        with patch.object(manager, 'create_execution_environment') as mock_create_env, \
             patch.object(manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Code execution step completed\nResults: {\'step\': \'code_execution\', \'status\': \'success\', \'pipeline_integration\': True}',
                'error': '',
                'exit_code': 0,
                'files_created': []
            }
            
            result = manager.execute_code(project_path, main_file)
            
            # Verify this step integrates properly in the pipeline
            self.assertTrue(result['success'])
            self.assertIn('Code execution step completed', result['output'])
            self.assertIn('pipeline_integration', result['output'])
    
    def test_execution_results_for_analysis(self):
        """Test that execution results are properly formatted for analysis step"""
        project_id = "TEST-ANALYSIS-001"
        project_path = self.temp_dir / project_id
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create code that generates analysis data
        main_file = code_dir / "main.py"
        main_file.write_text("""
import json

# Simulate data analysis
data = {
    'sample_size': 1000,
    'mean': 42.5,
    'std_dev': 8.2,
    'p_value': 0.03,
    'significant': True
}

print("Statistical analysis results:")
for key, value in data.items():
    print(f"  {key}: {value}")

# Save results for further analysis
with open('analysis_results.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Results saved to analysis_results.json")
""")
        
        manager = CodeExecutionManager(self.temp_dir)
        
        with patch.object(manager, 'create_execution_environment') as mock_create_env, \
             patch.object(manager, '_execute_in_venv') as mock_execute:
            
            mock_create_env.return_value = self.temp_dir / "mock_env"
            mock_execute.return_value = {
                'output': 'Statistical analysis results:\n  sample_size: 1000\n  mean: 42.5\n  std_dev: 8.2\n  p_value: 0.03\n  significant: True\nResults saved to analysis_results.json',
                'error': '',
                'exit_code': 0,
                'files_created': ['analysis_results.json']
            }
            
            result = manager.execute_code(project_path, main_file)
            
            # Verify the execution summary can be used for analysis
            execution_summary = f"""
## Code Execution Results
**Status:** {'Success' if result['success'] else 'Failed'}
**Runtime:** {result['runtime_seconds']:.2f}s
**Output:**
```
{result['output'][:500]}
```
**Error:**
```
{result['error'][:500]}
```"""
            
            # This is what would be passed to the analysis step
            self.assertIn('Statistical analysis results', execution_summary)
            self.assertIn('Success', execution_summary)
            self.assertIn('sample_size: 1000', execution_summary)


def run_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineExecutionFlow))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)