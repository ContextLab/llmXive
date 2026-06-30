"""
Unit tests for refactor_utils module.

Tests the code refactoring utilities including docstring standardization,
import consolidation, and unused import removal.
"""
import pytest
from pathlib import Path
import tempfile
import os
from code.refactor_utils import (
    standardize_docstring,
    consolidate_imports,
    remove_unused_imports,
    extract_used_names,
    clean_code_file,
    refactor_project,
    extract_used_names
)

class TestStandardizeDocstring:
    """Tests for the standardize_docstring function."""
    
    def test_none_docstring(self):
        """Test handling of None docstring."""
        result = standardize_docstring(None)
        assert '"""' in result
        assert 'placeholder' in result.lower()
    
    def test_empty_docstring(self):
        """Test handling of empty docstring."""
        result = standardize_docstring('')
        assert '"""' in result
    
    def test_simple_docstring(self):
        """Test standardization of a simple docstring."""
        doc = "This is a simple docstring."
        result = standardize_docstring(doc)
        assert result.startswith('"""')
        assert result.endswith('"""')
        assert 'This is a simple docstring.' in result
    
    def test_multiline_docstring(self):
        """Test standardization of a multiline docstring."""
        doc = """
        This is a multiline
        docstring with multiple lines.
        """
        result = standardize_docstring(doc)
        assert result.startswith('"""')
        assert result.endswith('"""')
        assert 'This is a multiline' in result
        assert 'docstring with multiple lines.' in result
    
    def test_docstring_with_whitespace(self):
        """Test handling of docstring with extra whitespace."""
        doc = """
            
            This has extra whitespace.
            
        """
        result = standardize_docstring(doc)
        assert 'This has extra whitespace.' in result
        # Should not have consecutive blank lines at start/end
        lines = result.split('\n')
        assert lines[0] == '"""'
        assert lines[-1] == '"""'

class TestConsolidateImports:
    """Tests for the consolidate_imports function."""
    
    def test_no_imports(self):
        """Test content with no imports."""
        content = """
        def hello():
            pass
        """
        result = consolidate_imports(content)
        assert 'def hello():' in result
    
    def test_single_import(self):
        """Test content with a single import."""
        content = "import os\n\ndef hello():\n    pass"
        result = consolidate_imports(content)
        assert 'import os' in result
    
    def test_multiple_imports_sorted(self):
        """Test that multiple imports are sorted."""
        content = """
        import sys
        import os
        import json
        """
        result = consolidate_imports(content)
        # Should be sorted alphabetically
        assert result.index('import json') < result.index('import os')
        assert result.index('import os') < result.index('import sys')
    
    def test_from_imports(self):
        """Test handling of from imports."""
        content = """
        from pathlib import Path
        import os
        """
        result = consolidate_imports(content)
        assert 'import os' in result
        assert 'from pathlib import Path' in result

class TestRemoveUnusedImports:
    """Tests for the remove_unused_imports function."""
    
    def test_remove_unused(self):
        """Test removal of unused imports."""
        content = """
        import os
        import sys
        import json
        
        def hello():
            print("Hello")
        """
        used_names = {'print'}
        result = remove_unused_imports(content, used_names)
        # All imports should be removed as none are used
        assert 'import os' not in result
        assert 'import sys' not in result
        assert 'import json' not in result
    
    def test_keep_used(self):
        """Test keeping used imports."""
        content = """
        import os
        import sys
        import json
        
        def hello():
            return os.path.join("a", "b")
        """
        used_names = {'os', 'path', 'join'}
        result = remove_unused_imports(content, used_names)
        # os should be kept
        assert 'import os' in result
        # sys and json should be removed
        assert 'import sys' not in result
        assert 'import json' not in result
    
    def test_from_import_partial(self):
        """Test partial removal in from imports."""
        content = """
        from os import path, sep, getcwd
        
        def hello():
            return path.join("a", "b")
        """
        used_names = {'path', 'join'}
        result = remove_unused_imports(content, used_names)
        # Only path should be kept
        assert 'from os import path' in result
        assert 'sep' not in result
        assert 'getcwd' not in result

class TestExtractUsedNames:
    """Tests for the extract_used_names function."""
    
    def test_simple_usage(self):
        """Test extraction of simple name usage."""
        content = """
        import os
        x = os.path.join("a", "b")
        """
        used = extract_used_names(content)
        assert 'os' in used
        assert 'x' in used
    
    def test_function_call(self):
        """Test extraction of function call usage."""
        content = """
        def hello():
            print("Hello")
        """
        used = extract_used_names(content)
        assert 'hello' in used
        assert 'print' in used
    
    def test_class_usage(self):
        """Test extraction of class usage."""
        content = """
        class MyClass:
            pass
        
        obj = MyClass()
        """
        used = extract_used_names(content)
        assert 'MyClass' in used
        assert 'obj' in used

class TestCleanCodeFile:
    """Tests for the clean_code_file function."""
    
    def test_clean_valid_file(self):
        """Test cleaning a valid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n\ndef hello():\n    pass\n")
            temp_path = Path(f.name)
        
        try:
            result = clean_code_file(temp_path, dry_run=True)
            assert result['success'] is True
            assert result['path'] == str(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_clean_invalid_file(self):
        """Test handling of invalid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def invalid(\n")  # Invalid syntax
            temp_path = Path(f.name)
        
        try:
            result = clean_code_file(temp_path, dry_run=True)
            # Should not crash, but may have issues
            assert result['path'] == str(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_clean_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = clean_code_file(Path('/nonexistent/file.py'), dry_run=True)
        assert result['success'] is False
        assert 'Could not read file' in str(result['issues_found'])

class TestRefactorProject:
    """Tests for the refactor_project function."""
    
    def test_refactor_empty_directory(self):
        """Test refactoring an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_dir = Path(tmpdir)
            results = refactor_project(code_dir, dry_run=True)
            assert len(results) == 0
    
    def test_refactor_with_files(self):
        """Test refactoring a directory with Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_dir = Path(tmpdir)
            
            # Create a Python file
            test_file = code_dir / "test.py"
            test_file.write_text("import os\n\ndef hello():\n    pass\n")
            
            results = refactor_project(code_dir, dry_run=True)
            assert len(results) == 1
            assert results[0]['path'] == str(test_file)
    
    def test_refactor_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        results = refactor_project(Path('/nonexistent/dir'), dry_run=True)
        assert len(results) == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])