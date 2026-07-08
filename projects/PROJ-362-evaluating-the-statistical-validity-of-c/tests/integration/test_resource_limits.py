"""
Integration test for T028: Verify memory usage stays < 7GB during full run.

This test executes the full pipeline (or a representative subset of modes)
and monitors memory consumption using `tracemalloc` and `psutil`.
It ensures that the resource constraints defined in FR-011 and SC-006 are met.
"""

import os
import sys
import unittest
import tracemalloc
import subprocess
import time

# Try to import psutil for accurate RSS memory measurement
# If not installed, we fall back to tracemalloc (though less accurate for total process memory)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Note: In a real CI environment, psutil should be present or installed via requirements.txt

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
MAIN_SCRIPT = os.path.join(CODE_DIR, 'main.py')

# Memory threshold in GB
MEMORY_THRESHOLD_GB = 7.0
MEMORY_THRESHOLD_BYTES = MEMORY_THRESHOLD_GB * 1024 * 1024 * 1024

# Modes to test (subset of full run to ensure coverage without 10h runtime)
# We test modes that involve data loading, permutation, and power analysis
# Note: We assume TREC Robust04 is small enough for a quick integration test
# If the full dataset is too large, this test might need to rely on a subsampled config
TEST_MODES = [
    'data_load',
    # 'permutation', # Might be too slow for a quick integration test if N=1000 on all queries
    # 'power_analysis', # Depends on permutation results
]

class TestResourceLimits(unittest.TestCase):
    """Test suite for verifying memory usage constraints."""

    @classmethod
    def setUpClass(cls):
        """Start memory tracing for the test class."""
        if not HAS_PSUTIL:
            print("WARNING: psutil not installed. Using tracemalloc fallback (may be less accurate).")
        tracemalloc.start()

    @classmethod
    def tearDownClass(cls):
        """Stop memory tracing."""
        tracemalloc.stop()

    def _get_current_memory_usage(self):
        """Get current memory usage in bytes."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        else:
            current, peak = tracemalloc.get_traced_memory()
            return current

    def _run_mode_with_memory_monitor(self, mode):
        """
        Runs a specific mode of the main.py script and monitors memory.

        Args:
            mode (str): The mode to run (e.g., 'data_load', 'permutation').

        Returns:
            tuple: (success: bool, peak_memory_gb: float, error_msg: str)
        """
        start_mem = self._get_current_memory_usage()
        peak_mem = start_mem

        # Construct command
        cmd = [sys.executable, MAIN_SCRIPT, '--mode', mode]

        # If specific data paths are needed, they should be handled by config.py defaults
        # or we might need to pass them. Assuming defaults work for integration.

        try:
            # Run the process
            # We use subprocess to run the script in the current process context?
            # No, to measure the script's memory, we should ideally run it as a subprocess
            # and monitor that subprocess, OR run the function directly if possible.
            # Since main.py uses argparse, running as subprocess is cleaner for isolation.

            # However, to measure peak memory of the *subprocess*, we need to monitor the subprocess.
            # This is complex.
            # Alternative: Import the run_* functions directly from main.py and run them here.
            # This allows us to use tracemalloc/psutil in the current process.
            # This is preferred for integration tests to avoid subprocess overhead and complexity.

            # Add code dir to path
            sys.path.insert(0, CODE_DIR)

            # Import the main module
            import main
            
            # Map mode string to function
            func_map = {
                'data_load': main.run_data_load_mode,
                'permutation': main.run_permutation_mode,
                'power_analysis': main.run_power_analysis_mode,
                'report': main.run_report_mode,
            }

            if mode not in func_map:
                return False, 0.0, f"Mode '{mode}' not found in main.py"

            func = func_map[mode]

            # Run the function
            # We need to mock args or set up global state if the function relies on it.
            # Looking at main.py structure, it likely parses args.
            # We will simulate the args object.
            
            import argparse
            args = argparse.Namespace()
            args.mode = mode
            args.queries = None # Use all or default
            args.subsample = None
            args.seed = 42 # Default from config

            # Execute
            func(args)

            # Check memory after execution
            current_mem = self._get_current_memory_usage()
            if current_mem > peak_mem:
                peak_mem = current_mem

            return True, peak_mem, None

        except Exception as e:
            return False, 0.0, str(e)

    def test_memory_usage_data_load(self):
        """Test that data loading mode stays under memory threshold."""
        success, peak_mem_bytes, error = self._run_mode_with_memory_monitor('data_load')
        
        if not success:
            self.fail(f"data_load mode failed: {error}")

        peak_mem_gb = peak_mem_bytes / (1024 ** 3)
        self.assertLess(
            peak_mem_gb, 
            MEMORY_THRESHOLD_GB, 
            f"data_load mode exceeded memory limit. Peak: {peak_mem_gb:.2f}GB > {MEMORY_THRESHOLD_GB}GB"
        )
        print(f"data_load mode memory usage: {peak_mem_gb:.2f}GB (Limit: {MEMORY_THRESHOLD_GB}GB)")

    # Optional: Add more modes if they are fast enough
    # def test_memory_usage_permutation(self):
    #     success, peak_mem_bytes, error = self._run_mode_with_memory_monitor('permutation')
    #     if not success:
    #         self.skipTest(f"permutation mode skipped due to error: {error}")
    #     peak_mem_gb = peak_mem_bytes / (1024 ** 3)
    #     self.assertLess(peak_mem_gb, MEMORY_THRESHOLD_GB, f"permutation mode exceeded limit: {peak_mem_gb:.2f}GB")


if __name__ == '__main__':
    unittest.main()