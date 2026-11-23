"""
Unit tests for the refactor cleanup utility.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, 'code')

from utils.refactor_cleanup import RefactorStats, CodeRefactorer


class TestRefactorStats:
    """Tests for RefactorStats class."""

    def test_initialization(self):
        """Test that stats are initialized to zero."""
        stats = RefactorStats()
        assert stats.files_processed == 0
        assert stats.files_modified == 0
        assert stats.total_lines_before == 0
        assert stats.dead_code_removed == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = RefactorStats()
        stats.files_processed = 5
        stats.files_modified = 3

        result = stats.to_dict()

        assert result['files_processed'] == 5
        assert result['files_modified'] == 3
        assert 'lines_removed' in result


class TestCodeRefactorer:
    """Tests for CodeRefactorer class."""

    @pytest.fixture
    def temp_code_dir(self):
        """Create a temporary directory with sample Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create sample file
            sample_file = tmpdir_path / "test_sample.py"
            sample_file.write_text("""
import os
import sys
import os

def test_function():
    return 1
    print("dead code")  # This is dead

def another_function():
    pass
""")
            yield tmpdir_path

    def test_find_python_files(self, temp_code_dir):
        """Test finding Python files in directory."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        files = refactoring._find_python_files()

        assert len(files) == 1
        assert files[0].name == "test_sample.py"

    def test_remove_dead_code(self, temp_code_dir):
        """Test removal of dead code after return statement."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        source = """
def test_function():
    return 1
    print("dead code")
"""
        new_source, removed_count = refactoring._remove_dead_code(source)

        assert "print" not in new_source
        assert removed_count == 1

    def test_standardize_imports(self, temp_code_dir):
        """Test standardization of imports."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        source = """
import sys
import os
import sys
import json
"""
        new_source, removed_count = refactoring._standardize_imports(source)

        # Should remove duplicate sys import
        assert removed_count == 1
        # Should have sorted imports
        lines = new_source.split('\n')
        import_lines = [l for l in lines if l.strip().startswith('import')]
        assert len(import_lines) == 3

    def test_fix_todo_comments(self, temp_code_dir):
        """Test fixing TODO comments."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        source = """
# TODO: fix this
def test():
    pass
"""
        new_source, fixed_count = refactoring._fix_todo_comments(source)

        assert fixed_count == 1
        assert "TODO: [T032]" in new_source

    def test_optimize_blank_lines(self, temp_code_dir):
        """Test optimization of blank lines."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        source = """




def test():
    pass
"""
        new_source, optimized_count = refactoring._optimize_blank_lines(source)

        # Should reduce multiple blank lines
        assert optimized_count > 0
        # Count consecutive blank lines
        lines = new_source.split('\n')
        max_consecutive = 0
        current = 0
        for line in lines:
            if not line.strip():
                current += 1
                max_consecutive = max(max_consecutive, current)
            else:
                current = 0
        assert max_consecutive <= 2

    def test_process_file(self, temp_code_dir):
        """Test processing a single file."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        file_path = temp_code_dir / "test_sample.py"

        result = refactoring._process_file(file_path)

        assert refactoring.stats.files_processed == 1

    def test_run(self, temp_code_dir):
        """Test running the full refactor process."""
        refactoring = CodeRefactorer(str(temp_code_dir), dry_run=True)
        report = refactoring.run()

        assert 'summary' in report
        assert report['summary']['files_processed'] >= 1
        assert Path('results/refactor_cleanup_report.json').exists()


class TestIntegration:
    """Integration tests for the refactor cleanup module."""

    def test_full_refactor_workflow(self):
        """Test the complete workflow with a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create a Python file with issues
            test_file = tmpdir_path / "test_issues.py"
            test_file.write_text("""
import sys
import os
import sys
import json

# TODO: fix this

def function_with_dead_code():
    return 1
    print("dead")
    print("also dead")

def another():
    pass
""")

            # Run refactoring
            refactoring = CodeRefactorer(str(tmpdir_path), dry_run=False)
            report = refactoring.run()

            # Verify report
            assert report['summary']['files_processed'] == 1
            assert report['summary']['files_modified'] == 1

            # Verify file was modified
            with open(test_file, 'r') as f:
                content = f.read()

            assert 'import sys' in content
            assert content.count('import sys') == 1  # No duplicates
            assert 'TODO: [T032]' in content
            assert 'print("dead")' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])