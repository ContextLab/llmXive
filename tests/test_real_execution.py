#!/usr/bin/env python3
"""
Real integration tests for llmXive code execution system
Creates actual virtual environments and executes real code
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
from typing import Dict, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


class TestRealCodeExecution(unittest.TestCase):
    """Real integration tests that create actual environments and run code"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - check system requirements"""
        print("\n" + "="*60)
        print("REAL EXECUTION TESTS - SYSTEM CHECK")
        print("="*60)
        
        # Check Python version
        python_version = sys.version_info
        print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        if python_version < (3, 8):
            raise unittest.SkipTest("Python 3.8+ required for real tests")
        
        # Check venv module
        try:
            import venv
            print("✅ venv module available")
        except ImportError:
            raise unittest.SkipTest("venv module not available")
        
        # Check subprocess functionality
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ subprocess working: {result.stdout.strip()}")
            else:
                raise unittest.SkipTest("subprocess not working properly")
        except Exception as e:
            raise unittest.SkipTest(f"subprocess error: {e}")
        
        print("✅ All system requirements met")
    
    def setUp(self):
        """Set up individual test"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_real_test_"))
        self.manager = CodeExecutionManager(self.temp_dir)
        print(f"\n🔧 Test directory: {self.temp_dir}")
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            print(f"🧹 Cleaning up: {self.temp_dir}")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_simple_python_execution(self):
        """Test real execution of simple Python code"""
        print("\n🧪 Testing simple Python execution")
        
        # Create project structure
        project_path = self.temp_dir / "simple_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create simple Python script
        main_script = code_dir / "main.py"
        main_script.write_text("""#!/usr/bin/env python3
import sys
import json
from datetime import datetime

print("=== Simple Python Test ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {__import__('os').getcwd()}")
print(f"Script location: {__file__}")

# Test basic functionality
result = {
    "test": "simple_python",
    "status": "success",
    "timestamp": datetime.now().isoformat(),
    "python_version": sys.version,
    "data": [1, 2, 3, 4, 5],
    "calculation": sum([1, 2, 3, 4, 5])
}

print(f"Calculation result: {result['calculation']}")

# Save result to file
with open("test_output.json", "w") as f:
    json.dump(result, f, indent=2)

print("Result saved to test_output.json")
print("=== Test Complete ===")
""")
        
        # Execute the code
        print("🚀 Executing simple Python script...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, main_script, timeout=60)
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution completed in {execution_time:.2f} seconds")
        
        # Verify results
        self.assertTrue(result['success'], f"Execution failed: {result['error']}")
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Simple Python Test', result['output'])
        self.assertIn('Test Complete', result['output'])
        
        # Verify output file was created
        output_file = project_path / "test_output.json"
        self.assertTrue(output_file.exists(), "Output file was not created")
        
        # Verify output file content
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        self.assertEqual(output_data['test'], 'simple_python')
        self.assertEqual(output_data['status'], 'success')
        self.assertEqual(output_data['calculation'], 15)
        
        # Verify execution reports were created
        json_report = project_path / "code" / "execution_report.json"
        md_report = project_path / "code" / "execution_report.md"
        
        self.assertTrue(json_report.exists(), "JSON execution report not created")
        self.assertTrue(md_report.exists(), "Markdown execution report not created")
        
        print("✅ Simple Python execution test passed")
    
    def test_real_python_with_packages(self):
        """Test real execution with package installation"""
        print("\n🧪 Testing Python with package dependencies")
        
        # Create project structure
        project_path = self.temp_dir / "package_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create requirements.txt with basic packages
        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("""# Basic scientific packages
numpy>=1.20.0
pandas>=1.3.0
""")
        
        # Create Python script that uses packages
        main_script = code_dir / "main.py"
        main_script.write_text("""#!/usr/bin/env python3
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

print("=== Package Dependencies Test ===")

# Test numpy
print("Testing NumPy...")
arr = np.array([1, 2, 3, 4, 5])
mean_val = np.mean(arr)
std_val = np.std(arr)
print(f"Array: {arr}")
print(f"Mean: {mean_val}")
print(f"Std: {std_val}")

# Test pandas
print("\\nTesting Pandas...")
df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
    'C': ['a', 'b', 'c', 'd', 'e']
})
print(f"DataFrame shape: {df.shape}")
print(f"DataFrame columns: {list(df.columns)}")
print(f"Sum of column A: {df['A'].sum()}")

# Save CSV file
df.to_csv('data_output.csv', index=False)
print("DataFrame saved to data_output.csv")

# Create result
result = {
    "test": "package_dependencies",
    "status": "success",
    "timestamp": datetime.now().isoformat(),
    "numpy_version": np.__version__,
    "pandas_version": pd.__version__,
    "array_mean": float(mean_val),
    "array_std": float(std_val),
    "dataframe_shape": df.shape,
    "dataframe_sum_A": int(df['A'].sum())
}

# Save result
with open("package_test_result.json", "w") as f:
    json.dump(result, f, indent=2)

print("\\n=== Package Test Complete ===")
print(f"NumPy version: {np.__version__}")
print(f"Pandas version: {pd.__version__}")
""")
        
        # Execute the code
        print("🚀 Executing Python script with package dependencies...")
        print("⚠️  This may take longer due to package installation...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, main_script, timeout=300)  # 5 minutes for package install
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution completed in {execution_time:.2f} seconds")
        
        # Verify results
        self.assertTrue(result['success'], f"Execution failed: {result['error']}")
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Package Dependencies Test', result['output'])
        self.assertIn('Package Test Complete', result['output'])
        
        # Verify output files were created
        csv_file = project_path / "data_output.csv"
        json_file = project_path / "package_test_result.json"
        
        self.assertTrue(csv_file.exists(), "CSV output file was not created")
        self.assertTrue(json_file.exists(), "JSON result file was not created")
        
        # Verify CSV content
        df_check = pd.read_csv(csv_file)
        self.assertEqual(df_check.shape, (5, 3))
        self.assertEqual(list(df_check.columns), ['A', 'B', 'C'])
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['test'], 'package_dependencies')
        self.assertEqual(result_data['status'], 'success')
        self.assertEqual(result_data['dataframe_sum_A'], 15)
        
        print("✅ Package dependencies test passed")
    
    def test_real_python_data_analysis(self):
        """Test real data analysis with visualization"""
        print("\n🧪 Testing real data analysis workflow")
        
        # Create project structure
        project_path = self.temp_dir / "analysis_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create requirements with visualization packages
        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("""numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.5.0
scipy>=1.7.0
""")
        
        # Create comprehensive analysis script
        main_script = code_dir / "main.py"
        main_script.write_text("""#!/usr/bin/env python3
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from scipy import stats
from datetime import datetime

print("=== Real Data Analysis Test ===")

# Generate synthetic dataset
np.random.seed(42)
n_samples = 1000

print(f"Generating {n_samples} samples...")
data = {
    'group': np.random.choice(['A', 'B', 'C'], n_samples),
    'value': np.random.normal(50, 15, n_samples),
    'score': np.random.uniform(0, 100, n_samples),
    'category': np.random.choice(['X', 'Y', 'Z'], n_samples)
}

df = pd.DataFrame(data)
print(f"Dataset created with shape: {df.shape}")

# Basic statistics
print("\\nCalculating basic statistics...")
basic_stats = df.describe()
print(basic_stats)

# Group analysis
print("\\nPerforming group analysis...")
group_means = df.groupby('group')['value'].mean()
group_stds = df.groupby('group')['value'].std()
print(f"Group means: {group_means.to_dict()}")
print(f"Group stds: {group_stds.to_dict()}")

# Statistical testing
print("\\nPerforming statistical tests...")
groups = [df[df['group'] == g]['value'].values for g in ['A', 'B', 'C']]
f_stat, p_value = stats.f_oneway(*groups)
print(f"ANOVA F-statistic: {f_stat:.4f}")
print(f"ANOVA p-value: {p_value:.4f}")

# Create visualizations
print("\\nCreating visualizations...")

# Create figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Data Analysis Results', fontsize=16)

# Histogram
axes[0, 0].hist(df['value'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
axes[0, 0].set_title('Distribution of Values')
axes[0, 0].set_xlabel('Value')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].grid(True, alpha=0.3)

# Box plot by group
df.boxplot(column='value', by='group', ax=axes[0, 1])
axes[0, 1].set_title('Values by Group')
axes[0, 1].set_xlabel('Group')
axes[0, 1].set_ylabel('Value')

# Scatter plot
colors = {'A': 'red', 'B': 'blue', 'C': 'green'}
for group in ['A', 'B', 'C']:
    group_data = df[df['group'] == group]
    axes[1, 0].scatter(group_data['value'], group_data['score'], 
                      c=colors[group], alpha=0.6, label=f'Group {group}')
axes[1, 0].set_title('Value vs Score by Group')
axes[1, 0].set_xlabel('Value')
axes[1, 0].set_ylabel('Score')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Group means bar plot
group_means.plot(kind='bar', ax=axes[1, 1], color=['red', 'blue', 'green'])
axes[1, 1].set_title('Mean Values by Group')
axes[1, 1].set_xlabel('Group')
axes[1, 1].set_ylabel('Mean Value')
axes[1, 1].tick_params(axis='x', rotation=0)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analysis_results.png', dpi=150, bbox_inches='tight')
plt.close()
print("Visualization saved as analysis_results.png")

# Save data
df.to_csv('analysis_data.csv', index=False)
print("Data saved as analysis_data.csv")

# Create comprehensive results
results = {
    "test": "real_data_analysis",
    "status": "success",
    "timestamp": datetime.now().isoformat(),
    "dataset_info": {
        "n_samples": len(df),
        "n_columns": len(df.columns),
        "columns": list(df.columns)
    },
    "statistics": {
        "overall_mean": float(df['value'].mean()),
        "overall_std": float(df['value'].std()),
        "group_means": {str(k): float(v) for k, v in group_means.items()},
        "group_stds": {str(k): float(v) for k, v in group_stds.items()}
    },
    "statistical_tests": {
        "anova_f_stat": float(f_stat),
        "anova_p_value": float(p_value),
        "significant": bool(p_value < 0.05)
    },
    "files_created": [
        "analysis_results.png",
        "analysis_data.csv",
        "analysis_results.json"
    ]
}

# Save results
with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\\n=== Analysis Summary ===")
print(f"Samples processed: {len(df)}")
print(f"Overall mean: {df['value'].mean():.2f}")
print(f"ANOVA significant: {p_value < 0.05}")
print(f"Files created: {len(results['files_created'])}")
print("=== Real Data Analysis Complete ===")
""")
        
        # Execute the code
        print("🚀 Executing comprehensive data analysis...")
        print("⚠️  This may take longer due to package installation and analysis...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, main_script, timeout=300)
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution completed in {execution_time:.2f} seconds")
        
        # Verify results
        self.assertTrue(result['success'], f"Execution failed: {result['error']}")
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Real Data Analysis Test', result['output'])
        self.assertIn('Real Data Analysis Complete', result['output'])
        
        # Verify all output files were created
        expected_files = [
            'analysis_results.png',
            'analysis_data.csv',
            'analysis_results.json'
        ]
        
        for filename in expected_files:
            file_path = project_path / filename
            self.assertTrue(file_path.exists(), f"Output file {filename} was not created")
            print(f"✅ Created: {filename} ({file_path.stat().st_size} bytes)")
        
        # Verify CSV data
        csv_file = project_path / "analysis_data.csv"
        df_check = pd.read_csv(csv_file)
        self.assertEqual(df_check.shape, (1000, 4))
        self.assertEqual(set(df_check.columns), {'group', 'value', 'score', 'category'})
        
        # Verify JSON results
        json_file = project_path / "analysis_results.json"
        with open(json_file, 'r') as f:
            analysis_results = json.load(f)
        
        self.assertEqual(analysis_results['test'], 'real_data_analysis')
        self.assertEqual(analysis_results['status'], 'success')
        self.assertEqual(analysis_results['dataset_info']['n_samples'], 1000)
        self.assertIn('anova_f_stat', analysis_results['statistical_tests'])
        
        # Verify PNG file exists and has reasonable size
        png_file = project_path / "analysis_results.png"
        png_size = png_file.stat().st_size
        self.assertGreater(png_size, 10000, "PNG file seems too small")  # At least 10KB
        
        print("✅ Real data analysis test passed")
    
    def test_real_error_handling(self):
        """Test real error handling and recovery"""
        print("\n🧪 Testing real error handling")
        
        # Create project structure
        project_path = self.temp_dir / "error_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create script with intentional errors
        error_script = code_dir / "main.py"
        error_script.write_text("""#!/usr/bin/env python3
import sys
print("Starting error test...")

# This will cause an import error
try:
    import non_existent_module_xyz123
except ImportError as e:
    print(f"Expected import error: {e}")

# This will cause a runtime error
print("About to cause division by zero...")
result = 10 / 0  # This will raise ZeroDivisionError
""")
        
        # Execute the code
        print("🚀 Executing script with intentional errors...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, error_script, timeout=60)
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution completed in {execution_time:.2f} seconds")
        
        # Verify error was captured
        self.assertFalse(result['success'], "Expected execution to fail")
        self.assertNotEqual(result['exit_code'], 0)
        self.assertIn('ZeroDivisionError', result['error'])
        
        # Verify partial output was captured
        self.assertIn('Starting error test', result['output'])
        self.assertIn('Expected import error', result['output'])
        
        # Verify error report was created
        json_report = project_path / "code" / "execution_report.json"
        md_report = project_path / "code" / "execution_report.md"
        
        self.assertTrue(json_report.exists(), "Error report JSON not created")
        self.assertTrue(md_report.exists(), "Error report markdown not created")
        
        # Verify error report content
        with open(json_report, 'r') as f:
            report = json.load(f)
        
        self.assertFalse(report['success'])
        self.assertIn('ZeroDivisionError', report['error'])
        
        print("✅ Real error handling test passed")
    
    def test_real_timeout_handling(self):
        """Test real timeout scenarios"""
        print("\n🧪 Testing real timeout handling")
        
        # Create project structure
        project_path = self.temp_dir / "timeout_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create script that runs longer than timeout
        timeout_script = code_dir / "main.py"
        timeout_script.write_text("""#!/usr/bin/env python3
import time
import sys

print("Starting timeout test...")
print("This script will run for 15 seconds...")

for i in range(15):
    print(f"Second {i+1}/15")
    time.sleep(1)

print("Script completed (this should not appear)")
""")
        
        # Execute with short timeout
        print("🚀 Executing script with 5-second timeout...")
        start_time = time.time()
        
        result = self.manager.execute_code(project_path, timeout_script, timeout=5)
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution stopped after {execution_time:.2f} seconds")
        
        # Verify timeout was handled
        self.assertFalse(result['success'], "Expected execution to timeout")
        self.assertIn('timed out', result['error'].lower())
        
        # Should have captured some output before timeout
        self.assertIn('Starting timeout test', result['output'])
        
        # Should not have the completion message
        self.assertNotIn('Script completed', result['output'])
        
        # Verify execution was actually stopped (should be close to 5 seconds)
        self.assertLess(execution_time, 8, "Execution took too long, timeout may not have worked")
        self.assertGreater(execution_time, 3, "Execution was too quick, may not have actually run")
        
        print("✅ Real timeout handling test passed")
    
    def test_real_environment_isolation(self):
        """Test that environments are properly isolated"""
        print("\n🧪 Testing real environment isolation")
        
        # Create two separate projects
        project1_path = self.temp_dir / "isolation_project1"
        project2_path = self.temp_dir / "isolation_project2"
        
        for project_path in [project1_path, project2_path]:
            code_dir = project_path / "code"
            code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create script that modifies environment in project 1
        script1 = project1_path / "code" / "main.py"
        script1.write_text("""#!/usr/bin/env python3
import os
import sys
import json

print("=== Environment Isolation Test - Project 1 ===")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")

# Create a file in the working directory
with open("project1_marker.txt", "w") as f:
    f.write("This file was created by project 1")

# Set an environment variable (this won't persist outside the execution)
os.environ["PROJECT1_VAR"] = "project1_value"

result = {
    "project": "project1",
    "python_executable": sys.executable,
    "working_directory": os.getcwd(),
    "env_var": os.environ.get("PROJECT1_VAR", "not_set"),
    "files_created": ["project1_marker.txt"]
}

with open("project1_result.json", "w") as f:
    json.dump(result, f, indent=2)

print("Project 1 execution complete")
""")
        
        # Create script for project 2
        script2 = project2_path / "code" / "main.py"
        script2.write_text("""#!/usr/bin/env python3
import os
import sys
import json

print("=== Environment Isolation Test - Project 2 ===")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")

# Check if project 1's file exists (it shouldn't in this directory)
project1_file_exists = os.path.exists("project1_marker.txt")
print(f"Project 1 marker file exists: {project1_file_exists}")

# Check if project 1's environment variable exists (it shouldn't)
project1_env_var = os.environ.get("PROJECT1_VAR", "not_found")
print(f"Project 1 env var: {project1_env_var}")

# Create our own file
with open("project2_marker.txt", "w") as f:
    f.write("This file was created by project 2")

result = {
    "project": "project2",
    "python_executable": sys.executable,
    "working_directory": os.getcwd(),
    "project1_file_exists": project1_file_exists,
    "project1_env_var": project1_env_var,
    "files_created": ["project2_marker.txt"]
}

with open("project2_result.json", "w") as f:
    json.dump(result, f, indent=2)

print("Project 2 execution complete")
""")
        
        # Execute both projects
        print("🚀 Executing project 1...")
        result1 = self.manager.execute_code(project1_path, script1, timeout=60)
        
        print("🚀 Executing project 2...")
        result2 = self.manager.execute_code(project2_path, script2, timeout=60)
        
        # Verify both executed successfully
        self.assertTrue(result1['success'], f"Project 1 failed: {result1['error']}")
        self.assertTrue(result2['success'], f"Project 2 failed: {result2['error']}")
        
        # Verify isolation - check project 1 results
        project1_result_file = project1_path / "project1_result.json"
        self.assertTrue(project1_result_file.exists())
        
        with open(project1_result_file, 'r') as f:
            project1_data = json.load(f)
        
        # Verify isolation - check project 2 results
        project2_result_file = project2_path / "project2_result.json"
        self.assertTrue(project2_result_file.exists())
        
        with open(project2_result_file, 'r') as f:
            project2_data = json.load(f)
        
        # Verify isolation worked
        self.assertFalse(project2_data['project1_file_exists'], 
                        "Project 1 file should not exist in project 2 directory")
        self.assertEqual(project2_data['project1_env_var'], 'not_found',
                        "Project 1 environment variable should not persist to project 2")
        
        # Verify files were created in correct locations
        self.assertTrue((project1_path / "project1_marker.txt").exists())
        self.assertTrue((project2_path / "project2_marker.txt").exists())
        self.assertFalse((project2_path / "project1_marker.txt").exists())
        self.assertFalse((project1_path / "project2_marker.txt").exists())
        
        print("✅ Real environment isolation test passed")


def run_real_tests():
    """Run all real integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestRealCodeExecution))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🚀 llmXive Real Code Execution Tests")
    print("=" * 60)
    print("⚠️  WARNING: These tests create real virtual environments")
    print("⚠️  WARNING: These tests install real packages")
    print("⚠️  WARNING: These tests may take several minutes")
    print("=" * 60)
    
    success = run_real_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL REAL TESTS PASSED!")
        print("✅ Code execution system verified with real environments")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ SOME REAL TESTS FAILED!")
        print("⚠️  Code execution system needs fixes")
        print("=" * 60)
        sys.exit(1)