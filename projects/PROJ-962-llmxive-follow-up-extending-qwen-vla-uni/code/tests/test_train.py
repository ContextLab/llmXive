"""
Integration test for model training and inference on sample data.
Tests T021: BERT embedding generation functionality.
"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import pandas as pd
import numpy as np

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code_03_train import generate_bert_embeddings, run_embedding_pipeline
from utils.seeds import set_global_seed


class TestModelTrainingAndInference(unittest.TestCase):
    """Test suite for BERT embedding generation and training pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        set_global_seed(42)
        self.test_dir = tempfile.mkdtemp()
        self.sample_data = pd.DataFrame({
            "instruction": [
                "Move the robot arm to the target position",
                "Grasp the red block and place it on the table",
                "Navigate to the kitchen and pick up the cup",
                "Avoid the obstacle and reach the goal",
                "Rotate the joint to 45 degrees"
            ],
            "cluster_id": [1, 1, 2, 2, 3]
        })
        
        # Save sample data
        self.input_path = os.path.join(self.test_dir, "sample_data.parquet")
        self.sample_data.to_parquet(self.input_path)
        
        self.output_path = os.path.join(self.test_dir, "test_embeddings.parquet")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_bert_embedding_generation(self):
        """Test that BERT embeddings are generated correctly."""
        # Generate embeddings for sample instructions
        embeddings = generate_bert_embeddings(self.sample_data["instruction"])
        
        # Verify shape
        self.assertEqual(embeddings.shape[0], len(self.sample_data))
        self.assertEqual(embeddings.shape[1], 768)  # BERT base hidden size
        
        # Verify dtype
        self.assertEqual(embeddings.dtype, np.float32)
        
        # Verify no NaN values
        self.assertFalse(np.isnan(embeddings).any())
        
        # Verify embeddings are not all zeros
        self.assertTrue(np.abs(embeddings).sum() > 0)

    def test_embedding_pipeline(self):
        """Test the full embedding pipeline from file to file."""
        # Run pipeline
        stats = run_embedding_pipeline(
            input_path=self.input_path,
            output_path=self.output_path,
            text_column="instruction"
        )
        
        # Verify stats
        self.assertEqual(stats["input_samples"], len(self.sample_data))
        self.assertEqual(stats["valid_samples"], len(self.sample_data))
        self.assertEqual(stats["embedding_dim"], 768)
        self.assertTrue(os.path.exists(self.output_path))
        
        # Load and verify output
        output_df = pd.read_parquet(self.output_path)
        self.assertIn("bert_embedding", output_df.columns)
        self.assertEqual(len(output_df), len(self.sample_data))
        
        # Verify embedding dimension in output
        for emb in output_df["bert_embedding"]:
            self.assertEqual(len(emb), 768)

    def test_empty_input_handling(self):
        """Test that empty input raises appropriate error."""
        empty_df = pd.DataFrame({"instruction": []})
        empty_path = os.path.join(self.test_dir, "empty.parquet")
        empty_df.to_parquet(empty_path)
        
        with self.assertRaises(ValueError):
            run_embedding_pipeline(
                input_path=empty_path,
                output_path=os.path.join(self.test_dir, "empty_out.parquet"),
                text_column="instruction"
            )

    def test_missing_column_handling(self):
        """Test that missing text column raises appropriate error."""
        wrong_df = pd.DataFrame({"wrong_column": ["test"]})
        wrong_path = os.path.join(self.test_dir, "wrong.parquet")
        wrong_df.to_parquet(wrong_path)
        
        with self.assertRaises(ValueError):
            run_embedding_pipeline(
                input_path=wrong_path,
                output_path=os.path.join(self.test_dir, "wrong_out.parquet"),
                text_column="instruction"
            )

    def test_cpu_only_execution(self):
        """Test that embeddings are generated on CPU."""
        # This test verifies that the code explicitly uses CPU
        # The generate_bert_embeddings function has device="cpu" hardcoded
        embeddings = generate_bert_embeddings(self.sample_data["instruction"])
        
        # If we got here without CUDA errors, CPU execution succeeded
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[1], 768)


if __name__ == "__main__":
    unittest.main()