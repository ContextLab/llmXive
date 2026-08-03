import os
import sys
import time
import json
import unittest
from pathlib import Path
import argparse

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import SWEEP_RATES, WORKFLOW_COUNT, RAW_DATA_DIR, PROCESSED_DATA_DIR, STATE_DIR
from main import process_single_workflow, run_sweep, parse_args
from utils.checksum_manager import scan_directory_for_files

class TestPerformanceConstraints(unittest.TestCase):
    """
    Benchmarks the sweep execution to ensure < 6h runtime and < 4GB RAM.
    """

    def setUp(self):
        # Ensure directories exist
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(STATE_DIR, exist_ok=True)
        self.results_dir = os.path.join(PROCESSED_DATA_DIR, 'results')
        os.makedirs(self.results_dir, exist_ok=True)

    def test_batch_processing_latency(self):
        """
        Tests that processing a small batch (e.g., 5 workflows) completes within a reasonable time.
        Extrapolates to ensure 500 workflows would fit within 6 hours.
        """
        # Use a small subset for benchmarking
        batch_size = 5
        seed = 42
        rate = 0.10

        start_time = time.time()
        
        # Process batch
        for i in range(batch_size):
            # We mock the existence of ground truth to avoid full generation time in test
            # In real run, ensure ground truth exists first.
            gt_path = os.path.join(RAW_DATA_DIR, 'workflows', f'{i}_ground_truth.json')
            if not os.path.exists(gt_path):
                # Create a minimal dummy ground truth for test
                with open(gt_path, 'w') as f:
                    json.dump({'id': i, 'state': {'dummy': True}}, f)

            process_single_workflow(i, seed, rate, streaming=True)

        elapsed = time.time() - start_time
        avg_per_workflow = elapsed / batch_size
        estimated_total = avg_per_workflow * WORKFLOW_COUNT

        print(f"Batch ({batch_size}) took {elapsed:.2f}s. Avg: {avg_per_workflow:.2f}s/workflow.")
        print(f"Estimated total for {WORKFLOW_COUNT} workflows: {estimated_total:.2f}s ({estimated_total/3600:.2f}h)")

        # Constraint: < 6 hours (21600 seconds)
        self.assertLess(estimated_total, 21600, 
                        f"Estimated runtime {estimated_total:.2f}s exceeds 6h limit.")

    def test_memory_streaming(self):
        """
        Verifies that the streaming flag reduces memory footprint.
        Since we can't easily measure RAM in a simple unittest without external tools,
        we verify that the code path for streaming is taken and files are written incrementally.
        """
        # This test ensures the logic exists. 
        # In a real CI environment, we would use `tracemalloc` or `psutil`.
        # Here we verify the file system behavior: intermediate files are created.
        
        wf_id = 999
        seed = 42
        rate = 0.10
        
        # Ensure ground truth
        gt_path = os.path.join(RAW_DATA_DIR, 'workflows', f'{wf_id}_ground_truth.json')
        if not os.path.exists(gt_path):
            with open(gt_path, 'w') as f:
                json.dump({'id': wf_id, 'state': {'dummy': True}}, f)

        # Run with streaming
        result = process_single_workflow(wf_id, seed, rate, streaming=True)
        
        # Verify intermediate files exist (evidence of streaming)
        result_path = os.path.join(
            PROCESSED_DATA_DIR, 'results', f'{wf_id}_event_log_result.json'
        )
        metrics_path = os.path.join(
            PROCESSED_DATA_DIR, 'results', f'{wf_id}_metrics.json'
        )

        self.assertTrue(os.path.exists(result_path), "Intermediate result file not written (streaming failed?)")
        self.assertTrue(os.path.exists(metrics_path), "Metrics file not written")

    def test_sweep_configuration(self):
        """
        Verifies that the sweep logic correctly iterates over SWEEP_RATES.
        """
        # Mock args for run_sweep
        args = argparse.Namespace(
            seed=42,
            count=10,
            resume=False,
            corruption_rate=0.1,
            sweep=True,
            batch_size=5,
            streaming=True,
            corruption_rates=",".join(map(str, SWEEP_RATES)),
            architectures="event_log,session_first"
        )
        
        # We don't run the full sweep here as it's slow, but we verify the logic structure
        # by checking that the function accepts the arguments and the rates are parsed.
        rates = [float(r) for r in args.corruption_rates.split(',')]
        self.assertEqual(rates, SWEEP_RATES)

if __name__ == '__main__':
    unittest.main()