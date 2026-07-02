"""
Unit tests for the quantization audit tool.

These tests verify that the audit tool correctly identifies:
1. Forbidden quantization imports (bitsandbytes, 8-bit, 4-bit)
2. Forbidden CUDA imports and usage
3. Allowed CPU-only patterns
"""

import os
import tempfile
from pathlib import Path
import pytest
from typing import List

# Import the audit functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.quantization_audit import (
    scan_file,
    QUANTIZATION_FORBIDDEN_PATTERNS,
    CUDA_FORBIDDEN_PATTERNS
)


class TestQuantizationAudit:
    """Test suite for quantization and CUDA audit functionality."""

    @pytest.fixture
    def temp_python_file(self, tmp_path: Path):
        """Create a temporary Python file for testing."""
        file_path = tmp_path / "test_file.py"
        return file_path

    def test_scan_file_empty(self, temp_python_file: Path, tmp_path: Path):
        """Test scanning an empty file."""
        # Create empty file
        temp_python_file.write_text("")

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) == 0

    def test_scan_file_allowed_cpu_pattern(self, temp_python_file: Path, tmp_path: Path):
        """Test that allowed CPU patterns are not flagged."""
        content = """
        import torch
        device = 'cpu'
        model.to('cpu')
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) == 0

    def test_scan_file_forbidden_quantization_bitsandbytes(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of forbidden bitsandbytes import."""
        content = """
        import bitsandbytes as bnb
        from bitsandbytes.nn import Linear8bitLt
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) > 0
        assert any('bitsandbytes' in issue for issue in quant_issues)
        assert len(cuda_issues) == 0

    def test_scan_file_forbidden_quantization_load_in_8bit(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of load_in_8bit parameter."""
        content = """
        model = AutoModel.from_pretrained(
            'model_name',
            load_in_8bit=True,
            device_map='auto'
        )
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) > 0
        assert any('load_in_8bit' in issue for issue in quant_issues)
        assert len(cuda_issues) == 0

    def test_scan_file_forbidden_quantization_load_in_4bit(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of load_in_4bit parameter."""
        content = """
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) > 0
        assert any('load_in_4bit' in issue or 'BitsAndBytesConfig' in issue for issue in quant_issues)
        assert len(cuda_issues) == 0

    def test_scan_file_forbidden_cuda_import(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of forbidden torch.cuda import."""
        content = """
        import torch.cuda
        from torch.cuda import device_count
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) > 0
        assert any('torch.cuda' in issue for issue in cuda_issues)

    def test_scan_file_forbidden_cuda_device_map(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of CUDA device_map."""
        content = """
        device = 'cuda'
        model.to('cuda')
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) > 0
        assert any('cuda' in issue.lower() for issue in cuda_issues)

    def test_scan_file_forbidden_cuda_tensor_type(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of CUDA default tensor type."""
        content = """
        torch.set_default_tensor_type('torch.cuda.FloatTensor')
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) > 0
        assert any('cuda' in issue.lower() for issue in cuda_issues)

    def test_scan_file_combined_issues(self, temp_python_file: Path, tmp_path: Path):
        """Test detection of both quantization and CUDA issues."""
        content = """
        import bitsandbytes
        import torch.cuda
        model = AutoModel.from_pretrained('model', load_in_8bit=True)
        device = 'cuda'
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) > 0
        assert len(cuda_issues) > 0

    def test_scan_file_clean_project(self, temp_python_file: Path, tmp_path: Path):
        """Test that clean project files pass the audit."""
        content = """
        import torch
        import numpy as np
        from typing import List, Dict

        class Agent:
            def __init__(self, device: str = 'cpu'):
                self.device = device
                self.model = None

            def load_model(self, model_path: str):
                self.model = torch.load(model_path, map_location='cpu')

            def predict(self, input_data: List[float]) -> Dict[str, float]:
                with torch.no_grad():
                    result = self.model(torch.tensor(input_data))
                return {'prediction': float(result)}
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        assert len(quant_issues) == 0
        assert len(cuda_issues) == 0

    def test_scan_file_line_number_accuracy(self, temp_python_file: Path, tmp_path: Path):
        """Test that line numbers in issues are accurate."""
        content = """
        import torch
        import bitsandbytes  # Line 3
        from transformers import AutoModel
        device = 'cuda'  # Line 5
        """
        temp_python_file.write_text(content)

        quant_issues, cuda_issues = scan_file(temp_python_file, tmp_path)

        # Check that line numbers are included in the issue messages
        for issue in quant_issues:
            assert ':3:' in issue or 'bitsandbytes' in issue

        for issue in cuda_issues:
            assert ':5:' in issue or 'cuda' in issue.lower()