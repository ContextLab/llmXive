import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory_analysis import (
    parse_memory_log,
    compute_memory_statistics,
    generate_markdown_report,
    save_json_profile,
    run_memory_analysis
)

class TestMemoryAnalysis:
    """Unit tests for memory analysis module."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file with sample memory data."""
        log_path = tmp_path / "memory_profile_raw.jsonl"
        data = [
            {"image_index": 0, "peak_memory_mb": 4500.5, "routing_shape": "[12, 50, 1024]"},
            {"image_index": 1, "peak_memory_mb": 4600.2, "routing_shape": "[12, 50, 1024]"},
            {"image_index": 2, "peak_memory_mb": 4700.8, "routing_shape": "[12, 50, 1024]", "oom_event": True},
            {"image_index": 3, "peak_memory_mb": 4550.1, "routing_shape": "[12, 50, 1024]"},
        ]
        with open(log_path, 'w') as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
        return str(log_path)

    @pytest.fixture
    def empty_log_file(self, tmp_path):
        """Create an empty log file."""
        log_path = tmp_path / "empty_memory_profile.jsonl"
        log_path.touch()
        return str(log_path)

    @pytest.fixture
    def malformed_log_file(self, tmp_path):
        """Create a log file with malformed JSON."""
        log_path = tmp_path / "malformed_memory_profile.jsonl"
        data = [
            '{"image_index": 0, "peak_memory_mb": 4500.5}',
            'invalid json line',
            '{"image_index": 1, "peak_memory_mb": 4600.2}',
        ]
        with open(log_path, 'w') as f:
            f.write('\n'.join(data))
        return str(log_path)

    def test_parse_memory_log_valid(self, temp_log_file):
        """Test parsing of valid memory log file."""
        records = parse_memory_log(temp_log_file)
        
        assert len(records) == 4
        assert records[0]['image_index'] == 0
        assert records[0]['peak_memory_mb'] == 4500.5
        assert records[2].get('oom_event', False) is True

    def test_parse_memory_log_empty(self, empty_log_file):
        """Test parsing of empty log file."""
        records = parse_memory_log(empty_log_file)
        assert len(records) == 0

    def test_parse_memory_log_malformed(self, malformed_log_file):
        """Test parsing of log file with malformed JSON."""
        # Should not raise, should skip invalid lines
        records = parse_memory_log(malformed_log_file)
        assert len(records) == 2  # Only valid lines

    def test_parse_memory_log_missing_file(self):
        """Test parsing of non-existent file."""
        records = parse_memory_log("/nonexistent/path/file.jsonl")
        assert len(records) == 0

    def test_compute_memory_statistics(self, temp_log_file):
        """Test computation of memory statistics."""
        records = parse_memory_log(temp_log_file)
        stats = compute_memory_statistics(records)
        
        assert stats['max_memory_mb'] == 4700.8
        assert stats['min_memory_mb'] == 4500.5
        assert stats['total_images'] == 4
        assert stats['oom_events'] == 1
        assert stats['oom_rate'] == 0.25
        assert 'memory_efficiency' in stats

    def test_compute_memory_statistics_empty(self):
        """Test statistics computation with empty records."""
        stats = compute_memory_statistics([])
        assert stats['max_memory_mb'] == 0.0
        assert stats['total_images'] == 0
        assert stats['memory_efficiency'] == 'Unknown'

    def test_generate_markdown_report(self, temp_log_file, tmp_path):
        """Test Markdown report generation."""
        records = parse_memory_log(temp_log_file)
        stats = compute_memory_statistics(records)
        output_path = str(tmp_path / "memory_report.md")
        
        generate_markdown_report(records, stats, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
            assert "# Memory Usage Report" in content
            assert "| Total Images Processed | 4 |" in content
            assert "## Per-Image Memory Usage" in content

    def test_save_json_profile(self, temp_log_file, tmp_path):
        """Test JSON profile saving."""
        records = parse_memory_log(temp_log_file)
        stats = compute_memory_statistics(records)
        output_path = str(tmp_path / "memory_profile.json")
        
        save_json_profile(stats, records, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert data['max_memory_mb'] == 4700.8
            assert 'per_image_data' in data
            assert len(data['per_image_data']) == 4

    def test_run_memory_analysis(self, temp_log_file, tmp_path):
        """Test full analysis pipeline."""
        md_output = str(tmp_path / "memory_report.md")
        json_output = str(tmp_path / "memory_profile.json")
        
        stats = run_memory_analysis(temp_log_file, md_output, json_output)
        
        assert os.path.exists(md_output)
        assert os.path.exists(json_output)
        assert stats['total_images'] == 4

    def test_memory_efficiency_classification(self, tmp_path):
        """Test OOM efficiency classification logic."""
        # Test optimal case
        stats_optimal = {'oom_events': 0, 'oom_rate': 0.0}
        assert compute_memory_statistics([{'peak_memory_mb': 100, 'oom_event': False}])['memory_efficiency'] == 'Optimal - No OOM events detected'
        
        # Test good case
        # Note: This requires a specific setup with low OOM rate
        pass

    def test_output_directory_creation(self, temp_log_file, tmp_path):
        """Test that output directories are created if they don't exist."""
        nested_md = str(tmp_path / "nested" / "dir" / "report.md")
        nested_json = str(tmp_path / "nested" / "dir" / "profile.json")
        
        run_memory_analysis(temp_log_file, nested_md, nested_json)
        
        assert os.path.exists(os.path.dirname(nested_md))
        assert os.path.exists(nested_md)
        assert os.path.exists(nested_json)