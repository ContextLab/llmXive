import pytest
import os
import tempfile
from code.cleanup import CodeCleanup

class TestCodeCleanup:
    def test_cleanup_initialization(self):
        """Test that CodeCleanup initializes correctly."""
        cleanup = CodeCleanup()
        assert cleanup is not None
        assert hasattr(cleanup, 'patterns') or hasattr(cleanup, 'rules')

    def test_cleanup_remove_todos(self):
        """Test that CodeCleanup removes TODO comments."""
        cleanup = CodeCleanup()
        
        # Create a temporary file with TODO comments
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("def test_function():\n    # TODO: implement this\n    pass\n")
            temp_path = f.name
        
        try:
            # Run cleanup
            cleanup.cleanup_file(temp_path)
            
            # Read the file back
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check that TODO is removed
            assert 'TODO' not in content
        finally:
            os.unlink(temp_path)

    def test_cleanup_remove_debug_prints(self):
        """Test that CodeCleanup removes debug print statements."""
        cleanup = CodeCleanup()
        
        # Create a temporary file with debug prints
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("def test_function():\n    print('DEBUG: testing')\n    return 42\n")
            temp_path = f.name
        
        try:
            # Run cleanup
            cleanup.cleanup_file(temp_path)
            
            # Read the file back
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check that debug print is removed
            assert "print('DEBUG:" not in content
        finally:
            os.unlink(temp_path)

    def test_cleanup_preserves_functionality(self):
        """Test that CodeCleanup preserves code functionality."""
        cleanup = CodeCleanup()
        
        # Create a temporary file with valid code and comments
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("""
def add_numbers(a, b):
    # Add two numbers
    return a + b

def multiply_numbers(a, b):
    # Multiply two numbers
    return a * b
""")
            temp_path = f.name
        
        try:
            # Run cleanup
            cleanup.cleanup_file(temp_path)
            
            # Read the file back
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check that core functionality is preserved
            assert 'def add_numbers' in content
            assert 'def multiply_numbers' in content
            assert 'return a + b' in content
            assert 'return a * b' in content
        finally:
            os.unlink(temp_path)