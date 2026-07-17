import unittest
import torch
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulation.training_loop import run_training_loop, TrainingLoopError
from config import get_path_str

class TestMemoryFootprint(unittest.TestCase):
    
    def test_training_loop_memory_limit(self):
        """
        Test that the training loop respects the memory limit (7GB).
        This is a functional test that runs a small loop and checks memory.
        """
        # We cannot easily simulate a memory overflow without massive data,
        # but we can verify the check_memory_limit function works and the loop runs.
        
        try:
            results = run_training_loop(
                epochs=1,
                bit_width=4,
                seed=42,
                output_dir=Path(get_path_str("results_dir"))
            )
            
            # Verify results structure
            self.assertIn("status", results)
            self.assertEqual(results["status"], "completed")
            
            # Verify memory snapshots are recorded
            self.assertIn("memory_snapshots", results)
            self.assertTrue(len(results["memory_snapshots"]) > 0)
            
            # Verify memory is within limit (7GB)
            for mem_gb in results["memory_snapshots"]:
                self.assertLessEqual(mem_gb, 7.0, f"Memory {mem_gb}GB exceeded limit")
                
        except TrainingLoopError as e:
            # If it fails due to memory, that's expected if the limit is tight,
            # but for this small test, it should pass.
            self.fail(f"Training loop raised unexpected memory error: {e}")

if __name__ == "__main__":
    unittest.main()
