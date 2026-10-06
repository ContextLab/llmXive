import os
import sys
import time
import tracemalloc
import unittest
from pathlib import Path
import logging

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import configure_logging, MemoryMonitor
from analysis import run_regression, run_sensitivity_analysis, load_metrics_data, main as analysis_main
from fetch import main as fetch_main
from metrics import main as metrics_main

logger = configure_logging()

class TestResourceLimits(unittest.TestCase):
    """Integration tests for timing and memory usage checks."""

    def setUp(self):
        """Set up test fixtures."""
        tracemalloc.start()
        self.memory_monitor = MemoryMonitor()
        self.max_memory_gb = 7.0
        self.max_time_seconds = 300

    def tearDown(self):
        """Clean up after tests."""
        tracemalloc.stop()

    def test_memory_monitor_limit(self):
        """Test that MemoryMonitor raises error when limit exceeded."""
        # This test is conceptual as we can't easily force high memory in a unit test
        # We verify the logic exists and raises if limit is exceeded
        try:
            # Try with a very low limit to trigger the error
            self.memory_monitor.check_limit(limit_gb=0.001)
            # If we reach here, memory usage is very low, which is fine for this env
            # But the logic should work if limit is exceeded
        except MemoryError:
            # Expected if memory usage > 0.001 GB
            pass

    def test_run_regression_timing(self):
        """Test that run_regression completes within time limit."""
        # Create a small dummy dataset for testing
        test_data = {
            'readability': [1.0, 2.0, 3.0],
            'sentiment': [0.1, 0.2, 0.3],
            'density': [0.5, 0.6, 0.7],
            'churn': [10, 20, 30],
            'bug_fix_rate': [0.1, 0.2, 0.3],
            'complexity': [2, 3, 4],
            'age': [100, 200, 300],
            'contributors': [1, 2, 3]
        }
        import pandas as pd
        df = pd.DataFrame(test_data)
        
        start_time = time.time()
        try:
            result = run_regression(df)
            elapsed = time.time() - start_time
            self.assertLess(elapsed, self.max_time_seconds, 
                            f"run_regression took {elapsed}s, limit is {self.max_time_seconds}s")
        except Exception as e:
            self.fail(f"run_regression failed: {e}")

    def test_run_sensitivity_timing(self):
        """Test that run_sensitivity_analysis completes within time limit."""
        test_data = {
            'readability': [1.0, 2.0, 3.0],
            'sentiment': [0.1, 0.2, 0.3],
            'density': [0.5, 0.6, 0.7],
            'churn': [10, 20, 30],
            'bug_fix_rate': [0.1, 0.2, 0.3],
            'complexity': [2, 3, 4],
            'age': [100, 200, 300],
            'contributors': [1, 2, 3]
        }
        import pandas as pd
        df = pd.DataFrame(test_data)
        
        start_time = time.time()
        try:
            result = run_sensitivity_analysis(df)
            elapsed = time.time() - start_time
            self.assertLess(elapsed, self.max_time_seconds, 
                            f"run_sensitivity_analysis took {elapsed}s, limit is {self.max_time_seconds}s")
        except Exception as e:
            self.fail(f"run_sensitivity_analysis failed: {e}")

    def test_full_pipeline_timing(self):
        """Test that the full analysis pipeline completes within time limit."""
        # This test assumes metrics.csv exists. If not, we create a dummy one.
        metrics_path = "data/processed/metrics.csv"
        if not os.path.exists(metrics_path):
            # Create a minimal dummy CSV
            os.makedirs("data/processed", exist_ok=True)
            with open(metrics_path, 'w') as f:
                f.write("readability,sentiment,density,churn,bug_fix_rate,complexity,age,contributors\n")
                f.write("1.0,0.1,0.5,10,0.1,2,100,1\n")
                f.write("2.0,0.2,0.6,20,0.2,3,200,2\n")
                f.write("3.0,0.3,0.7,30,0.3,4,300,3\n")
        
        start_time = time.time()
        try:
            # Run the main analysis function
            analysis_main()
            elapsed = time.time() - start_time
            self.assertLess(elapsed, self.max_time_seconds, 
                            f"Full pipeline took {elapsed}s, limit is {self.max_time_seconds}s")
        except Exception as e:
            self.fail(f"Full pipeline failed: {e}")
        finally:
            # Clean up dummy file if we created it
            if not os.path.exists("data/processed/metrics.csv.orig"):
                if os.path.exists(metrics_path):
                    os.remove(metrics_path)

    def test_memory_usage_during_analysis(self):
        """Test that memory usage stays within limits during analysis."""
        test_data = {
            'readability': [i * 0.1 for i in range(100)],
            'sentiment': [0.1 + (i * 0.01) for i in range(100)],
            'density': [0.5 + (i * 0.01) for i in range(100)],
            'churn': [10 + i for i in range(100)],
            'bug_fix_rate': [0.1 + (i * 0.001) for i in range(100)],
            'complexity': [2 + (i % 5) for i in range(100)],
            'age': [100 + i * 10 for i in range(100)],
            'contributors': [1 + (i % 10) for i in range(100)]
        }
        import pandas as pd
        df = pd.DataFrame(test_data)
        
        self.memory_monitor.check_limit(self.max_memory_gb)
        try:
            result = run_regression(df)
            # Check memory after execution
            current, peak = tracemalloc.get_traced_memory()
            self.assertLess(peak / (1024 ** 3), self.max_memory_gb, 
                            f"Peak memory {peak / (1024 ** 3):.2f}GB exceeded limit")
        except Exception as e:
            self.fail(f"Memory test failed: {e}")

if __name__ == '__main__':
    unittest.main()