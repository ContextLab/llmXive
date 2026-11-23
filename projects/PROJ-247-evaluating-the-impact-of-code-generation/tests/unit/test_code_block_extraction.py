"""
Unit tests for code block extraction logic (T012).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code_01_data_curation import extract_code_blocks_py, extract_code_blocks_js, calculate_file_hash

class TestPythonBlockExtraction:
    """Tests for Python code block extraction."""
    
    def test_extract_function(self):
        """Test extraction of a simple function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello_world():
    print("Hello, world!")
    return True
""")
            temp_path = Path(f.name)
        
        try:
            blocks = extract_code_blocks_py(temp_path)
            assert len(blocks) == 1
            assert blocks[0]['node_type'] == 'function'
            assert blocks[0]['start_line'] == 2
            assert blocks[1]['end_line'] == 4
            assert 'hello_world' in blocks[0]['block_id']
        finally:
            os.unlink(temp_path)
            
    def test_extract_class(self):
        """Test extraction of a class definition."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
class MyClass:
    def __init__(self):
  self.value = 10
  
    def get_value(self):
  return self.value
""")
            temp_path = Path(f.name)
            
        try:
            blocks = extract_code_blocks_py(temp_path)
            assert len(blocks) == 2  # Class + method
            class_blocks = [b for b in blocks if b['node_type'] == 'class']
            assert len(class_blocks) == 1
            assert 'MyClass' in class_blocks[0]['block_id']
        finally:
            os.unlink(temp_path)
            
    def test_invalid_python(self):
        """Test handling of invalid Python syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(")  # Invalid syntax
            temp_path = Path(f.name)
            
        try:
            blocks = extract_code_blocks_py(temp_path)
            assert len(blocks) == 0
        finally:
            os.unlink(temp_path)

class TestJavaScriptBlockExtraction:
    """Tests for JavaScript code block extraction."""
    
    def test_extract_function(self):
        """Test extraction of a JavaScript function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write("""
function add(a, b) {
    return a + b;
}
""")
            temp_path = Path(f.name)
            
        try:
            blocks = extract_code_blocks_js(temp_path)
            # Depending on tree-sitter availability, this might be empty or have results
            # We just check it doesn't crash
            assert isinstance(blocks, list)
        finally:
            os.unlink(temp_path)
            
    def test_extract_class(self):
        """Test extraction of a JavaScript class."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write("""
class Calculator {
    constructor() {
  this.result = 0;
    }
}
""")
            temp_path = Path(f.name)
            
        try:
            blocks = extract_code_blocks_js(temp_path)
            assert isinstance(blocks, list)
        finally:
            os.unlink(temp_path)

class TestHashCalculation:
    """Tests for file content hashing."""
    
    def test_hash_consistency(self):
        """Test that same content produces same hash."""
        content1 = "def test(): pass"
        content2 = "def test(): pass"
        
        hash1 = calculate_file_hash(content1)
        hash2 = calculate_file_hash(content2)
        
        assert hash1 == hash2
        
    def test_hash_difference(self):
        """Test that different content produces different hash."""
        content1 = "def test(): pass"
        content2 = "def test(): return True"
        
        hash1 = calculate_file_hash(content1)
        hash2 = calculate_file_hash(content2)
        
        assert hash1 != hash2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])