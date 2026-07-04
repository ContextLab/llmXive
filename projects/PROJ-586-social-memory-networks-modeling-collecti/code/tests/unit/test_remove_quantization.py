"""
Tests for T032: remove_quantization_imports.py
"""
import pathlib
import tempfile
import os
from code.remove_quantization_imports import is_prohibited_line, process_file

def test_quantization_imports_detected():
    """Test that quantization imports are detected."""
    lines = [
        "import bitsandbytes",
        "from bitsandbytes import nn",
        "from transformers import BitsAndBytesConfig",
        "load_in_8bit=True",
    ]
    for line in lines:
        is_bad, category = is_prohibited_line(line)
        assert is_bad, f"Line '{line}' should be detected as prohibited."
        assert category == "QUANTIZATION", f"Line '{line}' should be QUANTIZATION."

def test_cuda_imports_detected():
    """Test that CUDA usage is detected."""
    lines = [
        "import torch.cuda",
        "device = 'cuda'",
        "os.environ['CUDA_VISIBLE_DEVICES'] = '0'",
        "model.to('cuda')"
    ]
    for line in lines:
        is_bad, category = is_prohibited_line(line)
        assert is_bad, f"Line '{line}' should be detected as prohibited."
        assert category == "CUDA", f"Line '{line}' should be CUDA."

def test_clean_lines():
    """Test that clean lines are not flagged."""
    lines = [
        "import torch",
        "import numpy as np",
        "device = 'cpu'",
        "# This is a comment about cuda",
        "    # import bitsandbytes (commented out)",
    ]
    for line in lines:
        is_bad, _ = is_prohibited_line(line)
        assert not is_bad, f"Line '{line}' should not be flagged."

def test_process_file(tmp_path):
    """Test file processing."""
    # Create a temp file with violations
    test_file = tmp_path / "test.py"
    test_file.write_text("""
import torch
import bitsandbytes
device = 'cuda'
# comment
""")
    
    violations = process_file(test_file)
    assert len(violations) == 2
    assert any(v[1] == "QUANTIZATION" for v in violations)
    assert any(v[1] == "CUDA" for v in violations)

def test_process_file_clean(tmp_path):
    """Test file processing with clean file."""
    test_file = tmp_path / "clean.py"
    test_file.write_text("""
import torch
import numpy as np
device = 'cpu'
""")
    
    violations = process_file(test_file)
    assert len(violations) == 0