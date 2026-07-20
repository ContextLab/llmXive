"""
Unit tests for CPU compliance verification (T030).

These tests verify that the CPU compliance check correctly identifies
GPU-related code patterns and validates CPU-only libraries.
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.verify_cpu_compliance import (
    scan_file_for_gpu_usage,
    check_imports,
    GPU_PATTERNS
)


class TestCPUCompliance(unittest.TestCase):
    """Test cases for CPU compliance verification functions."""
    
    def test_scan_file_detects_torch_import(self):
        """Test that torch import is detected as GPU usage."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import torch\n")
            f.write("x = torch.randn(10)\n")
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertTrue(len(issues) > 0, "Should detect torch import")
            self.assertTrue(any('torch' in issue['pattern'] for issue in issues))
        finally:
            os.unlink(temp_path)
    
    def test_scan_file_detects_cuda_usage(self):
        """Test that .cuda() usage is detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import torch\n")
            f.write("x = torch.randn(10).cuda()\n")
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertTrue(len(issues) > 0, "Should detect .cuda() usage")
        finally:
            os.unlink(temp_path)
    
    def test_scan_file_detects_tensorflow(self):
        """Test that tensorflow import is detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import tensorflow as tf\n")
            f.write("with tf.device('/GPU:0'):\n")
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertTrue(len(issues) > 0, "Should detect tensorflow import")
        finally:
            os.unlink(temp_path)
    
    def test_scan_file_cpu_safe(self):
        """Test that CPU-safe code passes without issues."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import pandas as pd\n")
            f.write("import numpy as np\n")
            f.write("from statsmodels.tsa.stattools import grangercausalitytests\n")
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertEqual(len(issues), 0, "CPU-safe code should have no GPU issues")
        finally:
            os.unlink(temp_path)
    
    def test_check_imports_torch(self):
        """Test that torch import is flagged as unsafe."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import torch\n")
            f.write("from torch import nn\n")
            temp_path = f.name
        
        try:
            unsafe = check_imports(Path(temp_path))
            self.assertTrue(len(unsafe) > 0, "Should detect torch imports")
            self.assertTrue(any('torch' in imp for imp in unsafe))
        finally:
            os.unlink(temp_path)
    
    def test_check_imports_cpu_safe(self):
        """Test that CPU-safe imports are not flagged."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import pandas as pd\n")
            f.write("import numpy as np\n")
            f.write("from sklearn.linear_model import LinearRegression\n")
            f.write("import matplotlib.pyplot as plt\n")
            temp_path = f.name
        
        try:
            unsafe = check_imports(Path(temp_path))
            self.assertEqual(len(unsafe), 0, "CPU-safe imports should not be flagged")
        finally:
            os.unlink(temp_path)
    
    def test_gpu_patterns_list(self):
        """Test that GPU_PATTERNS list contains expected patterns."""
        self.assertIsInstance(GPU_PATTERNS, list)
        self.assertGreater(len(GPU_PATTERNS), 0)
        
        # Check for key patterns
        patterns_str = ' '.join(GPU_PATTERNS)
        self.assertIn('torch', patterns_str)
        self.assertIn('tensorflow', patterns_str)
        self.assertIn('cuda', patterns_str)
    
    def test_comment_lines_ignored(self):
        """Test that GPU patterns in comments are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# import torch  # This is a comment\n")
            f.write("# x = torch.randn(10).cuda()  # commented out\n")
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertEqual(len(issues), 0, "GPU patterns in comments should be ignored")
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Test handling of empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name
        
        try:
            issues = scan_file_for_gpu_usage(Path(temp_path))
            self.assertEqual(len(issues), 0, "Empty file should have no issues")
        finally:
            os.unlink(temp_path)
    
    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(\n")  # Syntax error
            temp_path = f.name
        
        try:
            unsafe = check_imports(Path(temp_path))
            # Should return empty list on syntax error, not crash
            self.assertIsInstance(unsafe, list)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()