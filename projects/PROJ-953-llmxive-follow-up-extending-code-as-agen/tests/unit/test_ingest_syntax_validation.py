import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Add code/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code' / 'scripts'))

from ingest import _is_valid_python_syntax, parse_swe_bench, parse_agent_bench

class TestSyntaxValidation:
    def test_valid_python(self):
        code = "def hello():\n    print('world')"
        assert _is_valid_python_syntax(code) is True

    def test_invalid_python_syntax(self):
        code = "def broken("
        assert _is_valid_python_syntax(code) is False

    def test_empty_string(self):
        assert _is_valid_python_syntax("") is False

    def test_none_input(self):
        assert _is_valid_python_syntax(None) is False

    def test_valid_single_line(self):
        code = "x = 1"
        assert _is_valid_python_syntax(code) is True

    def test_invalid_indentation(self):
        code = "def foo():\n    pass\nx=1\n y=2"
        assert _is_valid_python_syntax(code) is False

class TestParseSweBenchSyntaxHandling:
    def test_parse_with_valid_code(self):
        raw = [
            {
                'instance_id': 'test-1',
                'base_commit_code': 'def ok(): pass',
                'test_patch': 'def new(): pass'
            }
        ]
        parsed = parse_swe_bench(raw)
        assert len(parsed) == 1
        assert parsed[0]['is_unparseable'] is False
        assert parsed[0]['task_id'] == 'test-1'

    def test_parse_with_invalid_original_code(self):
        raw = [
            {
                'instance_id': 'test-2',
                'base_commit_code': 'def broken(', # Syntax error
                'test_patch': 'def new(): pass'
            }
        ]
        parsed = parse_swe_bench(raw)
        assert len(parsed) == 1
        assert parsed[0]['is_unparseable'] is True
        assert parsed[0]['task_id'] == 'test-2'

    def test_parse_with_empty_code(self):
        raw = [
            {
                'instance_id': 'test-3',
                'base_commit_code': '',
                'test_patch': ''
            }
        ]
        parsed = parse_swe_bench(raw)
        assert len(parsed) == 1
        assert parsed[0]['is_unparseable'] is True

class TestParseAgentBenchSyntaxHandling:
    def test_parse_with_valid_code(self):
        raw = [
            {
                'task_id': 'agent-1',
                'original_code': 'x = 1',
                'code_diff': 'y = 2'
            }
        ]
        parsed = parse_agent_bench(raw)
        assert len(parsed) == 1
        assert parsed[0]['is_unparseable'] is False

    def test_parse_with_invalid_code(self):
        raw = [
            {
                'task_id': 'agent-2',
                'original_code': 'x = ',
                'code_diff': 'y = 2'
            }
        ]
        parsed = parse_agent_bench(raw)
        assert len(parsed) == 1
        assert parsed[0]['is_unparseable'] is True