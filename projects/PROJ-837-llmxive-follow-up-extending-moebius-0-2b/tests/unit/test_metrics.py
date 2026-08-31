"""
Unit tests for code/eval/metrics.py
Tests FID, LPIPS, and latency calculation on CPU
"""
import os
import sys
import unittest
from pathlib import Path
import torch
import numpy as np
from PIL import Image

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.eval.metrics import (
    InpaintingEvalDataset,
    linalg_sqrtm,
    compute_fid,
    measure_inference_latency
)


class TestLinearAlgebraSqrtm(unittest.TestCase):
    """Tests for matrix square root calculation"""

    def test_sqrtm_identity(self):
        """Test sqrtm of identity matrix is identity"""
        I = torch.eye(3)
        result = linalg_sqrtm(I)
        self.assertTrue(torch.allclose(result, I, atol=1e-5))

    def test_sqrtm_positive_definite(self):
        """Test sqrtm on a positive definite matrix"""
        A = torch.tensor([[2.0, 1.0], [1.0, 2.0]])
        result = linalg_sqrtm(A)
        # Verify: result * result should equal A
        reconstructed = torch.mm(result, result)
        self.assertTrue(torch.allclose(reconstructed, A, atol=1e-4))

    def test_sqrtm_singular_matrix(self):
        """Test sqrtm handles singular matrix"""
        A = torch.tensor([[1.0, 0.0], [0.0, 0.0]])
        result = linalg_sqrtm(A)
        reconstructed = torch.mm(result, result)
        self.assertTrue(torch.allclose(reconstructed, A, atol=1e-4))


class TestFIDCalculation(unittest.TestCase):
    """Tests for FID (Fréchet Inception Distance) calculation"""

    def test_fid_zero_for_identical_distributions(self):
        """Test FID is 0 for identical distributions"""
        # Create two identical small distributions
        mu1 = torch.zeros(10)
        sigma1 = torch.eye(10)
        mu2 = torch.zeros(10)
        sigma2 = torch.eye(10)
        
        fid = compute_fid(mu1, sigma1, mu2, sigma2)
        self.assertAlmostEqual(fid.item(), 0.0, places=5)

    def test_fid_positive_for_different_distributions(self):
        """Test FID is positive for different distributions"""
        mu1 = torch.zeros(10)
        sigma1 = torch.eye(10)
        mu2 = torch.ones(10) * 2.0  # Different mean
        sigma2 = torch.eye(10)
        
        fid = compute_fid(mu1, sigma1, mu2, sigma2)
        self.assertGreater(fid.item(), 0)

    def test_fid_symmetric(self):
        """Test FID is symmetric"""
        mu1 = torch.randn(10)
        sigma1 = torch.eye(10) + 0.1 * torch.rand(10, 10)
        mu2 = torch.randn(10) * 2
        sigma2 = torch.eye(10) + 0.2 * torch.rand(10, 10)
        
        fid_12 = compute_fid(mu1, sigma1, mu2, sigma2)
        fid_21 = compute_fid(mu2, sigma2, mu1, sigma1)
        
        self.assertAlmostEqual(fid_12.item(), fid_21.item(), places=5)


class TestInferenceLatency(unittest.TestCase):
    """Tests for inference latency measurement"""

    def test_latency_positive(self):
        """Test that measured latency is positive"""
        def dummy_fn():
            time.sleep(0.01)  # 10ms sleep
        
        latency = measure_inference_latency(dummy_fn, n_runs=3)
        self.assertGreater(latency, 0)

    def test_latency_average(self):
        """Test that latency is average of multiple runs"""
        import time
        def dummy_fn():
            time.sleep(0.01)
        
        latency = measure_inference_latency(dummy_fn, n_runs=5)
        # Latency should be around 0.01s (10ms)
        self.assertGreater(latency, 0.005)
        self.assertLess(latency, 0.05)

    def test_latency_consistency(self):
        """Test that latency measurement is consistent"""
        def dummy_fn():
            pass  # Instant function
        
        latency1 = measure_inference_latency(dummy_fn, n_runs=10)
        latency2 = measure_inference_latency(dummy_fn, n_runs=10)
        
        # Both should be very small and close
        self.assertLess(latency1, 0.01)
        self.assertLess(latency2, 0.01)


class TestDatasetLoading(unittest.TestCase):
    """Tests for evaluation dataset loading"""

    def test_dataset_creation(self):
        """Test that dataset can be created"""
        # Create a temporary directory with dummy images
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy images
            for i in range(5):
                img = Image.new('RGB', (32, 32), color=(i*50, i*50, i*50))
                img.save(os.path.join(tmpdir, f'img_{i}.png'))
            
            dataset = InpaintingEvalDataset(root_dir=tmpdir)
            self.assertEqual(len(dataset), 5)

    def test_dataset_getitem(self):
        """Test that dataset returns correct items"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy images
            for i in range(3):
                img = Image.new('RGB', (32, 32), color=(255, 0, 0))
                img.save(os.path.join(tmpdir, f'img_{i}.png'))
            
            dataset = InpaintingEvalDataset(root_dir=tmpdir)
            item = dataset[0]
            self.assertIn('image', item)
            self.assertIn('path', item)

    def test_dataset_empty_directory(self):
        """Test dataset behavior with empty directory"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = InpaintingEvalDataset(root_dir=tmpdir)
            self.assertEqual(len(dataset), 0)


class TestMetricsCPU(unittest.TestCase):
    """Tests ensuring metrics work on CPU"""

    def test_fid_cpu(self):
        """Test FID calculation on CPU tensors"""
        mu1 = torch.zeros(10, device='cpu')
        sigma1 = torch.eye(10, device='cpu')
        mu2 = torch.ones(10, device='cpu')
        sigma2 = torch.eye(10, device='cpu')
        
        fid = compute_fid(mu1, sigma1, mu2, sigma2)
        self.assertEqual(fid.device.type, 'cpu')
        self.assertGreater(fid.item(), 0)

    def test_sqrtm_cpu(self):
        """Test sqrtm on CPU tensors"""
        A = torch.tensor([[2.0, 1.0], [1.0, 2.0]], device='cpu')
        result = linalg_sqrtm(A)
        self.assertEqual(result.device.type, 'cpu')


if __name__ == "__main__":
    unittest.main()
