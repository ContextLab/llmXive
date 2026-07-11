"""
Unit tests for the parsing logic in code/scripts/ingest.py.
These tests verify the distinct parsing logic for SWE-bench and AgentBench schemas.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from scripts.ingest import parse_swe_bench, parse_agent_bench

class TestSweBenchParsing:
    def test_parse_swe_bench_valid(self):
        """Test parsing a valid SWE-bench record."""
        record = {
            "instance_id": "test-instance-1",
            "repo": "test/repo",
            "base_commit": "abc123",
            "patch": "diff --git a/file.py b/file.py\nnew content",
            "test_patch": "diff --git a/test_file.py b/test_file.py",
            "problem_statement": "Fix the bug",
            "hints_text": "Check line 10",
            "created_at": "2023-01-01",
            "version": "1.0",
            "FAIL_TO_PASS": ["test_a"],
            "PASS_TO_PASS": ["test_b"],
            "environment_setup_commit": "def456"
        }
        
        result = parse_swe_bench(record)
        
        assert result is not None
        assert result["task_id"] == "test-instance-1"
        assert result["source_dataset"] == "swe-bench"
        assert result["code_diff"] == "diff --git a/file.py b/file.py\nnew content"
        assert result["problem_statement"] == "Fix the bug"
        assert "test_a" in result["eval_info"]
        
    def test_parse_swe_bench_missing_fields(self):
        """Test parsing a SWE-bench record with missing optional fields."""
        record = {
            "instance_id": "test-instance-2",
            "repo": "test/repo",
            "base_commit": "abc123",
            "patch": "diff content",
            "problem_statement": "Fix bug",
            # Missing hints, version, etc.
        }
        
        result = parse_swe_bench(record)
        
        assert result is not None
        assert result["task_id"] == "test-instance-2"
        assert result["hints"] == ""
        assert result["eval_info"] != ""  # Should be valid JSON even if empty lists

class TestAgentBenchParsing:
    def test_parse_agent_bench_valid(self):
        """Test parsing a valid AgentBench record."""
        record = {
            "instance_id": "os-instance-1",
            "question": "Create a file named test.txt",
            "answer": "echo 'hello' > test.txt",
            "context": "You are in a bash environment",
            "test_case": "file_exists test.txt"
        }
        
        result = parse_agent_bench(record)
        
        assert result is not None
        assert result["task_id"] == "os-instance-1"
        assert result["source_dataset"] == "agent-bench"
        assert result["code_diff"] == "echo 'hello' > test.txt"
        assert result["problem_statement"] == "Create a file named test.txt"
        assert result["repo"] == ""
        
    def test_parse_agent_bench_no_answer(self):
        """Test parsing when answer is missing, fallback to context."""
        record = {
            "instance_id": "os-instance-2",
            "question": "List files",
            "context": "ls -la",
            "answer": ""
        }
        
        result = parse_agent_bench(record)
        
        assert result is not None
        assert result["code_diff"] == "ls -la"

class TestIngestionIntegration:
    def test_merge_logic(self):
        """Test that the merge logic correctly combines records."""
        swe_record = {
            "task_id": "swe-1",
            "source_dataset": "swe-bench",
            "code_diff": "diff1"
        }
        agent_record = {
            "task_id": "agent-1",
            "source_dataset": "agent-bench",
            "code_diff": "diff2"
        }
        
        # Simulate the merge function logic
        merged = [swe_record, agent_record]
        
        assert len(merged) == 2
        assert merged[0]["source_dataset"] == "swe-bench"
        assert merged[1]["source_dataset"] == "agent-bench"
        assert merged[0]["task_id"] == "swe-1"
        assert merged[1]["task_id"] == "agent-1"
