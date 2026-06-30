import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from optimize_memory import MemoryOptimizer, main

class TestMemoryOptimizer(unittest.TestCase):
    
    def setUp(self):
        self.optimizer = MemoryOptimizer()
        
    def test_initial_batch_size(self):
        """Test that initial batch size is set correctly."""
        self.assertEqual(self.optimizer.batch_size, 1)  # Default from config or constant
        
    @patch("optimize_memory.resource.getrusage")
    def test_get_memory_usage_gb_linux(self, mock_getrusage):
        """Test memory usage calculation on Linux."""
        mock_getrusage.return_value.ru_maxrss = 1048576  # 1 GB in KB
        with patch("sys.platform", "linux"):
            usage = self.optimizer.get_memory_usage_gb()
            self.assertEqual(usage, 1.0)
            
    @patch("optimize_memory.resource.getrusage")
    def test_get_memory_usage_gb_macos(self, mock_getrusage):
        """Test memory usage calculation on macOS."""
        mock_getrusage.return_value.ru_maxrss = 2097152  # 2 GB in KB
        with patch("sys.platform", "darwin"):
            usage = self.optimizer.get_memory_usage_gb()
            self.assertEqual(usage, 2.0)
            
    def test_get_memory_usage_gb_windows_fallback(self):
        """Test memory usage calculation fallback on Windows."""
        with patch("sys.platform", "win32"):
            usage = self.optimizer.get_memory_usage_gb()
            self.assertEqual(usage, 0.0)  # Fallback value
            
    def test_adjust_batch_size_no_optimization_needed(self):
        """Test that batch size is not adjusted when duration is low."""
        current_batch, was_optimized = self.optimizer.adjust_batch_size(3.0)
        self.assertFalse(was_optimized)
        self.assertEqual(current_batch, self.optimizer.batch_size)
        
    def test_adjust_batch_size_optimization_triggered(self):
        """Test that batch size is reduced when duration is high."""
        current_batch, was_optimized = self.optimizer.adjust_batch_size(5.0)
        self.assertTrue(was_optimized)
        self.assertEqual(current_batch, 1)  # Reduced to 1
        
    def test_load_sample_memory_efficient_success(self):
        """Test successful loading of a sample."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Create a dummy file
            tmp.write(b"dummy_audio_data")
            tmp.flush()
            
        try:
            # Mock librosa.load to avoid actual audio processing
            with patch("optimize_memory.librosa.load") as mock_load:
                mock_load.return_value = ([0.1, 0.2, 0.3], 16000)
                
                result = self.optimizer.load_sample_memory_efficient(tmp_path)
                
                self.assertIsNotNone(result)
                self.assertIn("audio", result)
                self.assertIn("sample_rate", result)
                self.assertIn("path", result)
                self.assertEqual(result["sample_rate"], 16000)
        finally:
            tmp_path.unlink()
            
    def test_load_sample_memory_efficient_failure(self):
        """Test handling of failed sample loading."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"dummy_data")
            tmp.flush()
            
        try:
            with patch("optimize_memory.librosa.load", side_effect=Exception("Load failed")):
                result = self.optimizer.load_sample_memory_efficient(tmp_path)
                self.assertIsNone(result)
        finally:
            tmp_path.unlink()
            
    def test_run_optimization_check_success(self):
        """Test successful optimization check with benchmark data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_path = Path(tmpdir) / "benchmark_duration.json"
            report_path = Path(tmpdir) / "optimization_report.json"
            
            # Create benchmark data with high duration
            benchmark_data = {
                "duration_hours": 5.0,
                "original_batch_size": 4
            }
            with open(benchmark_path, 'w') as f:
                json.dump(benchmark_data, f)
                
            # Temporarily override paths for the optimizer
            original_batch = self.optimizer.batch_size
            self.optimizer.batch_size = 4
            
            report = self.optimizer.run_optimization_check(benchmark_path)
            
            self.assertEqual(report["status"], "optimized")
            self.assertTrue(report["was_optimized"])
            self.assertEqual(report["optimized_batch_size"], 1)
            
            # Restore
            self.optimizer.batch_size = original_batch
            
    def test_run_optimization_check_missing_file(self):
        """Test handling of missing benchmark file."""
        missing_path = Path("/nonexistent/path/benchmark.json")
        report = self.optimizer.run_optimization_check(missing_path)
        self.assertEqual(report["status"], "error")
        self.assertIn("not found", report["message"])

if __name__ == "__main__":
    unittest.main()
