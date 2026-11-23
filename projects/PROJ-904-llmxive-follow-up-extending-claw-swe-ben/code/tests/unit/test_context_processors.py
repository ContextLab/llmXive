import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.context_processors import (
    retrieve_diff_aware_snippets,
    fallback_strategy,
    process_context,
    log_fallback,
    ContextSnippet
)
from config import get_data_dir

class TestDiffAwareWindowProcessor:
    def test_retrieves_keywords(self):
        """Test that diff_aware retrieves snippets around keywords."""
        repo_files = {
            "main.py": "def fix_bug():\n    pass\n\ndef another():\n    # TODO: implement\n    pass"
        }
        issue = "Fix the bug"
        
        snippets = retrieve_diff_aware_snippets(issue, repo_files, window_size=1)
        
        assert len(snippets) > 0
        assert any("fix_bug" in s.content for s in snippets)
    
    def test_returns_empty_on_no_keywords(self):
        """Test that diff_aware returns empty list if no keywords are found."""
        repo_files = {
            "main.py": "def normal_function():\n    x = 1\n    return x"
        }
        issue = "This is a purely textual description without code context."
        
        snippets = retrieve_diff_aware_snippets(issue, repo_files, window_size=5)
        
        assert len(snippets) == 0

class TestFallbackStrategy:
    def test_fallback_on_empty_diff(self):
        """
        T051 Verification: Create a unit test that mocks an issue with no code changes
        and verifies the fallback occurs and logs correctly.
        """
        repo_files = {
            "test_file.py": "line1\nline2\nline3\nline4\nline5"
        }
        instance_id = "test-instance-123"
        
        # Call process_context with diff_aware strategy on issue with no keywords
        issue_text = "Purely textual issue with no code keywords."
        
        # This should trigger the fallback logic inside process_context
        result = process_context(issue_text, repo_files, "diff_aware", instance_id)
        
        # Verify the strategy switched to first_n_lines
        assert result.strategy == "first_n_lines"
        assert len(result.snippets) == 1
        assert "line1" in result.snippets[0].content
    
    def test_fallback_logs_to_file(self):
        """Verify that the fallback event is logged to data/audit_logs/fallbacks.jsonl."""
        # Create a temporary directory for testing to avoid polluting real data
        # We mock get_data_dir to return a temp path
        original_get_data_dir = get_data_dir
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch get_data_dir temporarily
            import data.context_processors as cp_module
            cp_module.get_data_dir = lambda: Path(tmpdir)
            
            try:
                repo_files = {"test.py": "def bug(): pass"}
                issue = "Text only"
                instance_id = "log-test-001"
                
                # Trigger fallback
                process_context(issue, repo_files, "diff_aware", instance_id)
                
                # Check log file
                audit_file = Path(tmpdir) / "audit_logs" / "fallbacks.jsonl"
                assert audit_file.exists(), "Fallback log file was not created"
                
                with open(audit_file, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) > 0, "Fallback log file is empty"
                    
                    entry = json.loads(lines[-1])
                    assert entry["instance_id"] == instance_id
                    assert entry["original_strategy"] == "diff_aware"
                    assert entry["fallback_strategy"] == "first_n_lines"
                    assert "No hunks" in entry["reason"] or "No snippets" in entry["reason"]
            finally:
                # Restore original
                cp_module.get_data_dir = original_get_data_dir
    
    def test_fallback_with_real_repo(self):
        """Test fallback strategy directly with a valid repo."""
        repo_files = {
            "utils.py": "def helper():\n    return True"
        }
        ctx = fallback_strategy("test-001", repo_files, n_lines=2)
        
        assert ctx.strategy == "first_n_lines"
        assert len(ctx.snippets) == 1
        assert "helper" in ctx.snippets[0].content
        assert ctx.snippets[0].start_line == 0
        assert ctx.snippets[0].end_line == 2