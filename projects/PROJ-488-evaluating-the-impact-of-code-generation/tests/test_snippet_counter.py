import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snippet_counter import load_processed_snippets, count_valid_snippets, verify_snippet_counts, ERROR_104

class TestSnippetCounter:
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)
            yield data_dir

    def test_count_valid_snippets(self):
        """Test counting valid snippets."""
        snippets = [
            {"id": "1", "code": "def foo(): pass", "language": "python"},
            {"id": "2", "code": "def bar(): pass", "language": "python"},
            {"id": "3", "code": "def baz(): pass", "language": "javascript"}, # Invalid language
            {"id": "4", "code": "missing language key"}, # Missing language
            {"id": "5", "code": "missing id"}, # Missing id
            {"id": "6", "code": "valid", "language": "python"}
        ]
        count = count_valid_snippets(snippets)
        assert count == 3

    def test_count_empty_list(self):
        """Test counting with empty list."""
        assert count_valid_snippets([]) == 0

    def test_load_processed_snippets_success(self, temp_data_dir):
        """Test loading snippets from a valid file."""
        file_path = temp_data_dir / "processed" / "test_group_snippets.json"
        data = [
            {"id": "1", "code": "x=1", "language": "python"}
        ]
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_processed_snippets(temp_data_dir, "test_group")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_load_processed_snippets_not_found(self, temp_data_dir):
        """Test loading snippets when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_processed_snippets(temp_data_dir, "non_existent_group")

    def test_verify_snippet_counts_pass(self, temp_data_dir):
        """Test verification passing with sufficient snippets."""
        # Create two groups with 1001 snippets each
        for group in ["group_a", "group_b"]:
            file_path = temp_data_dir / "processed" / f"{group}_snippets.json"
            snippets = [
                {"id": str(i), "code": f"code_{i}", "language": "python"}
                for i in range(1001)
            ]
            with open(file_path, 'w') as f:
                json.dump(snippets, f)
        
        # Should not raise an exception
        result = verify_snippet_counts(temp_data_dir, ["group_a", "group_b"], min_count=1000)
        assert result is True

    def test_verify_snippet_counts_fail(self, temp_data_dir):
        """Test verification failing with insufficient snippets."""
        # Create one group with 1001 and one with 999
        file_path_a = temp_data_dir / "processed" / "group_a_snippets.json"
        snippets_a = [
            {"id": str(i), "code": f"code_{i}", "language": "python"}
            for i in range(1001)
        ]
        with open(file_path_a, 'w') as f:
            json.dump(snippets_a, f)

        file_path_b = temp_data_dir / "processed" / "group_b_snippets.json"
        snippets_b = [
            {"id": str(i), "code": f"code_{i}", "language": "python"}
            for i in range(999)
        ]
        with open(file_path_b, 'w') as f:
            json.dump(snippets_b, f)
        
        # Should raise SystemExit with code 104
        with pytest.raises(SystemExit) as exc_info:
            verify_snippet_counts(temp_data_dir, ["group_a", "group_b"], min_count=1000)
        
        assert exc_info.value.code == ERROR_104

    def test_verify_snippet_counts_missing_file(self, temp_data_dir):
        """Test verification failing when a file is missing."""
        # Create only one group file
        file_path_a = temp_data_dir / "processed" / "group_a_snippets.json"
        snippets_a = [
            {"id": str(i), "code": f"code_{i}", "language": "python"}
            for i in range(1001)
        ]
        with open(file_path_a, 'w') as f:
            json.dump(snippets_a, f)
        
        # Should raise SystemExit with code 104 due to missing group_b file
        with pytest.raises(SystemExit) as exc_info:
            verify_snippet_counts(temp_data_dir, ["group_a", "group_b"], min_count=1000)
        
        assert exc_info.value.code == ERROR_104
