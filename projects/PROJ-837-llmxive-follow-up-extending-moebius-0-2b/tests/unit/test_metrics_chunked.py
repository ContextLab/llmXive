import os
import json
import tempfile
from pathlib import Path
import unittest
import numpy as np
from PIL import Image
import torch
import torch.nn as nn

# Add project root to path if needed
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.eval.metrics import (
    InpaintingEvalDataset,
    compute_fid,
    compute_lpips,
    evaluate_model,
    run_metrics_evaluation,
    CHUNK_SIZE,
    BATCH_SIZE_FID
)
from code.utils.seed import set_seed

class MockModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 3, 1)
    
    def forward(self, x):
        return self.conv(x) + x

class TestMetricsChunked(unittest.TestCase):
    def setUp(self):
        set_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.masked_dir = Path(self.temp_dir) / "masked"
        self.original_dir = Path(self.temp_dir) / "original"
        self.masked_dir.mkdir()
        self.original_dir.mkdir()

        # Create dummy images
        for i in range(10):
            img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            Image.fromarray(img).save(self.masked_dir / f"img_{i}_masked.png")
            Image.fromarray(img).save(self.original_dir / f"img_{i}_original.png")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_dataset_creation(self):
        dataset = InpaintingEvalDataset(str(self.masked_dir), str(self.original_dir))
        self.assertEqual(len(dataset), 10)
        img1, img2, id_ = dataset[0]
        self.assertEqual(img1.shape, (3, 64, 64))

    def test_compute_fid(self):
        real = np.random.randn(100, 512)
        fake = np.random.randn(100, 512)
        fid = compute_fid(real, fake)
        self.assertIsInstance(fid, float)
        self.assertTrue(fid >= 0)

    def test_evaluate_model_memory_efficiency(self):
        """
        Test that evaluate_model processes data in chunks without OOM.
        We simulate a large dataset by creating many small images.
        """
        model = MockModel()
        model.eval()
        
        # Create a larger dataset to test chunking
        for i in range(20):
            img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            Image.fromarray(img).save(self.masked_dir / f"large_img_{i}_masked.png")
            Image.fromarray(img).save(self.original_dir / f"large_img_{i}_original.png")

        dataset = InpaintingEvalDataset(str(self.masked_dir), str(self.original_dir))
        # Use a DataLoader with batch size larger than chunk size to force internal chunking logic
        # Note: The evaluate_model function internally manages batching for feature extraction
        from torch.utils.data import DataLoader
        dataloader = DataLoader(dataset, batch_size=BATCH_SIZE_FID, shuffle=False)

        # This should run without memory error
        results = evaluate_model(model, dataloader, device="cpu")
        
        self.assertIn("fid", results)
        self.assertIn("lpips", results)
        self.assertIn("latency", results)
        self.assertIsNotNone(results["fid"])

    def test_run_metrics_evaluation_io(self):
        """
        Test that run_metrics_evaluation writes a valid JSON file.
        """
        model = MockModel()
        model.eval()
        
        output_path = Path(self.temp_dir) / "test_results.json"
        
        results = run_metrics_evaluation(
            model=model,
            masked_dir=str(self.masked_dir),
            original_dir=str(self.original_dir),
            output_path=str(output_path),
            device="cpu"
        )
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        self.assertEqual(saved_results, results)
        self.assertIn("fid", saved_results)

if __name__ == "__main__":
    unittest.main()