"""
Integration tests for full data loading and schema validation.

This module verifies the end-to-end correctness of:
1. `create_streaming_loader`: Ensures the loader yields valid MoleculeData objects.
2. Schema Validation: Ensures all required attributes (x, pos, y, scaffold_id) exist and have correct dtypes/shapes.
3. "Fail Loudly" logic: Ensures the loader raises RuntimeError if real data fetch fails.

Execution: Run `python -m pytest tests/test_loader.py::TestIntegrationDataLoading -v`
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.loader import create_streaming_loader, run_memory_probe, adaptive_sample_size
from data.dataset import MoleculeData
from data.preprocess import apply_scaffold_split
from utils import set_seed, get_logger

# Import the internal fetch logic to mock it for the "Fail Loudly" test
# We assume the implementation uses a helper to fetch the dataset
from datasets import load_dataset

logger = get_logger(__name__)


class TestIntegrationDataLoading(unittest.TestCase):
    """Integration tests for the full data loading pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.test_dir = tempfile.mkdtemp()
        self.logger = logger

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_pipeline_schema_validation(self):
        """
        Integration test: Load a small real sample of QM9 (streaming) and validate schema.
        
        Steps:
        1. Initialize streaming loader for QM9 (Merz-Kollman subset).
        2. Iterate through a fixed number of samples (e.g., 10).
        3. Validate that each sample is an instance of MoleculeData.
        4. Validate attributes: x (int), pos (float), y (float), scaffold_id (str).
        5. Validate shapes (e.g., x shape [N, 1], pos shape [N, 3], y shape [N, 1]).
        """
        try:
            # We use a small target to ensure we don't OOM on CI runners
            # and to speed up the test.
            target_gb = 0.1 
            batch_size = 16
            
            # Calculate adaptive sample size
            max_samples = adaptive_sample_size(batch_size, target_gb)
            # Cap at 50 for this specific integration test to ensure speed
            max_samples = min(max_samples, 50)

            if max_samples <= 0:
                self.fail("Adaptive sample size calculation resulted in 0 or negative samples.")

            # Create the loader
            # Note: We assume the loader fetches 'qm9' with specific features.
            # The exact dataset config depends on the implementation in loader.py.
            # We assume a standard 'qm9' dataset from HuggingFace with 'merzkollman' split or similar.
            # Since the real dataset might be large, we rely on streaming=True.
            
            # We need to ensure the loader is configured to fetch the correct subset.
            # For this test, we assume the loader handles the 'qm9' dataset with
            # the necessary charge columns.
            
            loader = create_streaming_loader(
                dataset_name="qm9",
                config_name="default", # Adjust if a specific config is needed for charges
                split="train",         # Start with train split
                streaming=True,
                max_samples=max_samples,
                batch_size=batch_size
            )

            count = 0
            for batch in loader:
                count += 1
                
                # Validate batch type
                self.assertIsInstance(batch, MoleculeData, "Batch must be an instance of MoleculeData")
                
                # Validate attributes exist
                self.assertTrue(hasattr(batch, 'x'), "Missing attribute 'x'")
                self.assertTrue(hasattr(batch, 'pos'), "Missing attribute 'pos'")
                self.assertTrue(hasattr(batch, 'y'), "Missing attribute 'y'")
                self.assertTrue(hasattr(batch, 'scaffold_id'), "Missing attribute 'scaffold_id'")

                # Validate dtypes
                self.assertEqual(batch.x.dtype, torch.long, f"x dtype is {batch.x.dtype}, expected torch.long")
                self.assertEqual(batch.pos.dtype, torch.float32, f"pos dtype is {batch.pos.dtype}, expected torch.float32")
                self.assertEqual(batch.y.dtype, torch.float32, f"y dtype is {batch.y.dtype}, expected torch.float32")

                # Validate shapes
                # x: [num_nodes, num_features] (usually num_nodes, 1 for atomic number)
                self.assertEqual(len(batch.x.shape), 2, f"x shape {batch.x.shape} is not 2D")
                self.assertEqual(batch.x.shape[1], 1, f"x feature dim is {batch.x.shape[1]}, expected 1")
                
                # pos: [num_nodes, 3]
                self.assertEqual(len(batch.pos.shape), 2, f"pos shape {batch.pos.shape} is not 2D")
                self.assertEqual(batch.pos.shape[1], 3, f"pos feature dim is {batch.pos.shape[1]}, expected 3")
                
                # y: [num_nodes, 1] (charges)
                self.assertEqual(len(batch.y.shape), 2, f"y shape {batch.y.shape} is not 2D")
                self.assertEqual(batch.y.shape[1], 1, f"y feature dim is {batch.y.shape[1]}, expected 1")

                # Validate scaffold_id is a string or list of strings
                if isinstance(batch.scaffold_id, torch.Tensor):
                    # If it's a tensor, it might be a list of strings encoded or just a single ID for the batch
                    # But typically scaffold_id is a string per molecule in the graph
                    # If the batch contains multiple molecules, this might be a list or a tensor of IDs
                    # For a single molecule graph batch, it should be a string or tensor of length 1
                    pass
                else:
                    self.assertIsInstance(batch.scaffold_id, (str, list), f"scaffold_id type is {type(batch.scaffold_id)}")

                # Check for non-null charges (y should not contain NaN)
                self.assertFalse(torch.isnan(batch.y).any(), "Found NaN in charge values (y)")
                
                # Check for valid coordinates (pos should not contain NaN)
                self.assertFalse(torch.isnan(batch.pos).any(), "Found NaN in coordinates (pos)")

            self.assertGreater(count, 0, "Loader yielded no batches")
            self.logger.info(f"Successfully validated {count} batches from real data stream.")

        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            raise

    def test_fail_loudly_on_fetch_failure(self):
        """
        Integration test: Verify that the loader raises RuntimeError if the real data fetch fails.
        
        This test mocks the underlying dataset loading mechanism to simulate a network failure
        or missing dataset, ensuring the system does NOT fall back to synthetic data.
        """
        # We patch the load_dataset function to raise an exception
        with patch('data.loader.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Simulated network failure: Dataset not reachable.")
            
            # We expect the create_streaming_loader to propagate this error
            # OR raise a specific RuntimeError wrapping it, as per "Fail Loudly" requirement.
            # The implementation in loader.py should catch generic errors and re-raise as RuntimeError
            # or let the specific error bubble up if it's a network issue.
            
            with self.assertRaises(RuntimeError) as context:
                loader = create_streaming_loader(
                    dataset_name="qm9",
                    config_name="default",
                    split="train",
                    streaming=True,
                    max_samples=10,
                    batch_size=16
                )
                # Force an iteration to trigger the fetch
                for _ in loader:
                    pass
            
            # Verify the error message indicates a real data failure, not a synthetic fallback
            self.assertIn("real data", str(context.exception).lower() or "fetch failed", 
                          "Error message should indicate a real data fetch failure.")

    def test_scaffold_split_integration(self):
        """
        Integration test: Verify that scaffold split indices are correctly applied to the loader.
        
        This test ensures that the split logic from T009a works in conjunction with the loader.
        """
        # 1. Generate split indices (mocked or real, but we need the function to exist)
        # Since we are testing the loader's consumption of splits, we assume the split logic
        # produces valid indices.
        
        # For this integration test, we will create a small mock dataset that mimics the structure
        # and verify that the loader respects the split indices if passed.
        # However, the loader implementation likely handles the split internally or via a filter.
        
        # We will test the apply_scaffold_split function with a small mock stream
        # and then verify the loader can consume the result.
        
        # Create a small mock dataset
        mock_data_list = []
        for i in range(20):
            # Create a minimal MoleculeData
            mol = MoleculeData(
                x=torch.tensor([[6]] * 5), # 5 carbons
                pos=torch.rand(5, 3),
                y=torch.rand(5, 1),
                scaffold_id=f"scaffold_{i % 5}" # 5 unique scaffolds
            )
            mock_data_list.append(mol)
        
        # Apply split (this function should return iterators)
        # We assume the function takes a list of molecules and returns train/val/test iterators
        # The exact signature depends on T009a implementation
        # Assuming: apply_scaffold_split(data_list, seed=42) -> (train_iter, val_iter, test_iter)
        
        # We need to import the function from preprocess
        from data.preprocess import apply_scaffold_split
        
        try:
            train_iter, val_iter, test_iter = apply_scaffold_split(mock_data_list, seed=42)
            
            # Verify we get iterators
            self.assertTrue(hasattr(train_iter, '__iter__'))
            self.assertTrue(hasattr(val_iter, '__iter__'))
            self.assertTrue(hasattr(test_iter, '__iter__'))
            
            # Verify we can consume them
            train_list = list(train_iter)
            val_list = list(val_iter)
            test_list = list(test_iter)
            
            total = len(train_list) + len(val_list) + len(test_list)
            self.assertEqual(total, 20, "Split did not preserve all molecules")
            
            # Verify no overlap (scaffolds should be disjoint)
            train_scaffolds = set(m.scaffold_id for m in train_list)
            val_scaffolds = set(m.scaffold_id for m in val_list)
            test_scaffolds = set(m.scaffold_id for m in test_list)
            
            self.assertTrue(train_scaffolds.isdisjoint(val_scaffolds), "Train and Val scaffolds overlap")
            self.assertTrue(train_scaffolds.isdisjoint(test_scaffolds), "Train and Test scaffolds overlap")
            self.assertTrue(val_scaffolds.isdisjoint(test_scaffolds), "Val and Test scaffolds overlap")
            
            logger.info("Scaffold split integration test passed.")
            
        except Exception as e:
            logger.error(f"Scaffold split integration test failed: {e}")
            raise


if __name__ == '__main__':
    unittest.main()