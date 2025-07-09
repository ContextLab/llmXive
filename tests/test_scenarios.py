#!/usr/bin/env python3
"""
Test scenarios for manual testing of code execution system
Creates realistic test projects and executes them
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


class TestScenarios:
    """Creates and runs various test scenarios"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_test_"))
        self.manager = CodeExecutionManager(self.temp_dir)
        print(f"Test directory: {self.temp_dir}")
    
    def cleanup(self):
        """Clean up test directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"Cleaned up: {self.temp_dir}")
    
    def create_python_data_analysis_project(self) -> Path:
        """Create a realistic Python data analysis project"""
        project_path = self.temp_dir / "python_data_analysis"
        project_path.mkdir(parents=True)
        
        # Create requirements.txt
        requirements = """numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.5.0
seaborn>=0.11.0
scipy>=1.7.0
"""
        (project_path / "requirements.txt").write_text(requirements)
        
        # Create main analysis script
        main_script = """#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json

def generate_sample_data():
    \"\"\"Generate sample data for analysis\"\"\"
    np.random.seed(42)
    
    # Create sample dataset
    n_samples = 1000
    data = {
        'group': np.random.choice(['A', 'B', 'C'], n_samples),
        'value': np.random.normal(50, 15, n_samples),
        'category': np.random.choice(['X', 'Y', 'Z'], n_samples),
        'score': np.random.uniform(0, 100, n_samples)
    }
    
    return pd.DataFrame(data)

def analyze_data(df):
    \"\"\"Perform statistical analysis\"\"\"
    print("=== Data Analysis Results ===")
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Basic statistics
    print("\\n--- Basic Statistics ---")
    print(df.describe())
    
    # Group analysis
    print("\\n--- Group Analysis ---")
    group_stats = df.groupby('group')['value'].agg(['mean', 'std', 'count'])
    print(group_stats)
    
    # Correlation analysis
    print("\\n--- Correlation Analysis ---")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_matrix = df[numeric_cols].corr()
    print(correlation_matrix)
    
    # Statistical tests
    print("\\n--- Statistical Tests ---")
    groups = [df[df['group'] == g]['value'].values for g in ['A', 'B', 'C']]
    f_stat, p_value = stats.f_oneway(*groups)
    print(f"ANOVA F-statistic: {f_stat:.4f}, p-value: {p_value:.4f}")
    
    return {
        'sample_size': len(df),
        'groups': group_stats.to_dict(),
        'correlation': correlation_matrix.to_dict(),
        'anova_f_stat': f_stat,
        'anova_p_value': p_value,
        'significant': p_value < 0.05
    }

def create_visualizations(df, results):
    \"\"\"Create data visualizations\"\"\"
    print("\\n=== Creating Visualizations ===")
    
    # Set style
    plt.style.use('seaborn-v0_8')
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Data Analysis Results', fontsize=16)
    
    # Histogram
    axes[0, 0].hist(df['value'], bins=30, alpha=0.7, color='skyblue')
    axes[0, 0].set_title('Distribution of Values')
    axes[0, 0].set_xlabel('Value')
    axes[0, 0].set_ylabel('Frequency')
    
    # Box plot by group
    df.boxplot(column='value', by='group', ax=axes[0, 1])
    axes[0, 1].set_title('Values by Group')
    
    # Scatter plot
    scatter = axes[1, 0].scatter(df['value'], df['score'], c=df['group'].astype('category').cat.codes, alpha=0.6)
    axes[1, 0].set_title('Value vs Score')
    axes[1, 0].set_xlabel('Value')
    axes[1, 0].set_ylabel('Score')
    
    # Correlation heatmap
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_matrix = df[numeric_cols].corr()
    im = axes[1, 1].imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
    axes[1, 1].set_title('Correlation Matrix')
    axes[1, 1].set_xticks(range(len(numeric_cols)))
    axes[1, 1].set_yticks(range(len(numeric_cols)))
    axes[1, 1].set_xticklabels(numeric_cols)
    axes[1, 1].set_yticklabels(numeric_cols)
    
    # Add colorbar
    plt.colorbar(im, ax=axes[1, 1])
    
    # Save figure
    plt.tight_layout()
    plt.savefig('analysis_results.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Visualization saved as analysis_results.png")

def save_results(results):
    \"\"\"Save analysis results to JSON\"\"\"
    with open('analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to analysis_results.json")

def main():
    \"\"\"Main analysis function\"\"\"
    print("Starting data analysis...")
    
    # Generate and analyze data
    df = generate_sample_data()
    results = analyze_data(df)
    
    # Create visualizations
    create_visualizations(df, results)
    
    # Save results
    save_results(results)
    
    print("\\n=== Analysis Complete ===")
    print(f"Processed {len(df)} samples")
    print(f"ANOVA significant: {results['significant']}")
    print("Files created: analysis_results.png, analysis_results.json")
    
    return results

if __name__ == "__main__":
    results = main()
"""
        
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        (code_dir / "main.py").write_text(main_script)
        
        return project_path
    
    def create_simple_python_project(self) -> Path:
        """Create a simple Python project for basic testing"""
        project_path = self.temp_dir / "simple_python"
        project_path.mkdir(parents=True)
        
        # Simple main script
        main_script = """#!/usr/bin/env python3
import json
import os
from datetime import datetime

def main():
    print("Simple Python project test")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {os.sys.executable}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Create a simple result
    result = {
        "project": "simple_python",
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "test_passed": True
    }
    
    # Save result
    with open("test_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("Test result saved to test_result.json")
    print("Simple Python project test complete!")
    
    return result

if __name__ == "__main__":
    result = main()
    print(f"Final result: {result}")
"""
        
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        (code_dir / "main.py").write_text(main_script)
        
        return project_path
    
    def create_error_project(self) -> Path:
        """Create a project that will fail for error testing"""
        project_path = self.temp_dir / "error_project"
        project_path.mkdir(parents=True)
        
        # Script with intentional errors
        error_script = """#!/usr/bin/env python3
import non_existent_module  # This will cause ImportError
import json

def main():
    print("This should not print due to import error")
    
    # This would also cause an error
    undefined_variable = some_undefined_var
    
    # This would cause another error
    result = {"test": "value"}
    return result

if __name__ == "__main__":
    main()
"""
        
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        (code_dir / "main.py").write_text(error_script)
        
        return project_path
    
    def create_r_project(self) -> Path:
        """Create an R project for multi-language testing"""
        project_path = self.temp_dir / "r_project"
        project_path.mkdir(parents=True)
        
        # R analysis script
        r_script = """#!/usr/bin/env Rscript
# Simple R analysis script
library(stats)

# Generate sample data
set.seed(42)
n <- 1000
data <- data.frame(
  x = rnorm(n, mean = 50, sd = 10),
  y = rnorm(n, mean = 30, sd = 5),
  group = sample(c("A", "B", "C"), n, replace = TRUE)
)

# Basic statistics
cat("=== R Analysis Results ===\\n")
cat("Data shape:", dim(data), "\\n")
cat("Summary statistics:\\n")
print(summary(data))

# T-test
group_a <- data$x[data$group == "A"]
group_b <- data$x[data$group == "B"]
t_result <- t.test(group_a, group_b)

cat("\\nT-test results:\\n")
print(t_result)

# Save results
results <- list(
  sample_size = n,
  mean_x = mean(data$x),
  mean_y = mean(data$y),
  t_statistic = t_result$statistic,
  p_value = t_result$p.value,
  significant = t_result$p.value < 0.05
)

# Save to JSON (if jsonlite is available)
if (require("jsonlite", quietly = TRUE)) {
  write_json(results, "r_results.json", pretty = TRUE)
  cat("Results saved to r_results.json\\n")
} else {
  cat("Results: ", results, "\\n")
}

cat("R analysis complete!\\n")
"""
        
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        (code_dir / "main.R").write_text(r_script)
        
        return project_path
    
    def run_scenario_test(self, project_path: Path, scenario_name: str) -> Dict:
        """Run a test scenario and return results"""
        print(f"\n{'='*60}")
        print(f"RUNNING SCENARIO: {scenario_name}")
        print(f"{'='*60}")
        
        # Find main file
        main_files = []
        code_dir = project_path / "code"
        
        for pattern in ["main.py", "main.R", "main.jl", "index.js"]:
            main_file = code_dir / pattern
            if main_file.exists():
                main_files.append(main_file)
        
        if not main_files:
            print("❌ No main file found!")
            return {"error": "No main file found"}
        
        main_file = main_files[0]
        print(f"📄 Main file: {main_file}")
        
        # Show project structure
        print("\n📁 Project structure:")
        for item in sorted(project_path.rglob("*")):
            if item.is_file():
                relative_path = item.relative_to(project_path)
                print(f"  {relative_path}")
        
        # Execute the project
        try:
            print(f"\n🚀 Executing {scenario_name}...")
            result = self.manager.execute_code(project_path, main_file, timeout=30)
            
            print(f"\n📊 EXECUTION RESULTS:")
            print(f"Success: {result['success']}")
            print(f"Exit code: {result['exit_code']}")
            print(f"Runtime: {result['runtime_seconds']:.2f}s")
            
            if result['output']:
                print(f"\n📄 OUTPUT:")
                print(result['output'])
            
            if result['error']:
                print(f"\n❌ ERRORS:")
                print(result['error'])
            
            if result['files_created']:
                print(f"\n📁 FILES CREATED:")
                for file in result['files_created']:
                    print(f"  {file}")
            
            # Check for execution reports
            report_files = [
                project_path / "code" / "execution_report.json",
                project_path / "code" / "execution_report.md"
            ]
            
            for report_file in report_files:
                if report_file.exists():
                    print(f"✅ Report created: {report_file}")
                else:
                    print(f"❌ Report missing: {report_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ EXECUTION ERROR: {e}")
            return {"error": str(e), "success": False}
    
    def run_all_scenarios(self):
        """Run all test scenarios"""
        print("🧪 Running all test scenarios...")
        
        scenarios = [
            ("Simple Python", self.create_simple_python_project),
            ("Python Data Analysis", self.create_python_data_analysis_project),
            ("Error Project", self.create_error_project),
            ("R Project", self.create_r_project),
        ]
        
        results = {}
        
        for scenario_name, create_func in scenarios:
            try:
                # Create project
                project_path = create_func()
                
                # Run scenario
                result = self.run_scenario_test(project_path, scenario_name)
                results[scenario_name] = result
                
            except Exception as e:
                print(f"❌ Failed to create scenario {scenario_name}: {e}")
                results[scenario_name] = {"error": str(e), "success": False}
        
        # Print summary
        print(f"\n{'='*60}")
        print("SCENARIO SUMMARY")
        print(f"{'='*60}")
        
        for scenario_name, result in results.items():
            success = result.get('success', False)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{scenario_name}: {status}")
            
            if not success and 'error' in result:
                print(f"  Error: {result['error']}")
        
        return results


def main():
    """Main function to run test scenarios"""
    print("🚀 llmXive Code Execution Test Scenarios")
    print("=" * 60)
    
    scenarios = TestScenarios()
    
    try:
        results = scenarios.run_all_scenarios()
        
        # Calculate success rate
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results.values() if r.get('success', False))
        
        print(f"\n🎯 FINAL RESULTS: {passed_scenarios}/{total_scenarios} scenarios passed")
        
        if passed_scenarios == total_scenarios:
            print("🎉 All scenarios passed!")
            return 0
        else:
            print("⚠️  Some scenarios failed. Review the output above.")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1
    
    finally:
        scenarios.cleanup()


if __name__ == "__main__":
    sys.exit(main())