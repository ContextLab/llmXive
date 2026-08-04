"""
Unit tests for mpstat_parser.py
"""
import pytest
from orchestrator.mpstat_parser import parse_mpstat_output, get_aggregated_utilization


class TestMpstatParser:
    """Tests for the mpstat output parser."""

    def test_parse_standard_output(self):
        """Test parsing a standard mpstat output string."""
        sample_output = """
        Linux 5.15.0-46-generic (node1) 	10/25/2023 	_x86_64_	(4 CPU)

        10:00:00 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        10:00:01 AM  all    2.50    0.00    1.00    0.50    0.00    0.00    0.00    0.00    0.00   96.00
        10:00:02 AM  all    5.00    0.00    2.00    1.00    0.00    0.00    0.00    0.00    0.00   92.00

        Average:      CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        Average:      all    3.75    0.00    1.50    0.75    0.00    0.00    0.00    0.00    0.00   94.00
        """
        
        result = parse_mpstat_output(sample_output)
        
        assert len(result) == 2  # Two data lines (excluding Average)
        
        # Check first line
        assert result[0]["cpu_id"] == "all"
        assert result[0]["cpu_utilization_pct"] == 4.0  # 100 - 96
        assert result[0]["idle_pct"] == 96.0
        assert "10:00:01 AM" in result[0]["timestamp"]

    def test_parse_single_cpu(self):
        """Test parsing output with specific CPU cores."""
        sample_output = """
        10:00:00 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        10:00:01 AM  0      10.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00   90.00
        10:00:01 AM  1      20.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00   80.00
        """
        
        result = parse_mpstat_output(sample_output)
        
        assert len(result) == 2
        assert result[0]["cpu_id"] == "0"
        assert result[0]["cpu_utilization_pct"] == 10.0
        assert result[1]["cpu_id"] == "1"
        assert result[1]["cpu_utilization_pct"] == 20.0

    def test_parse_empty_output_raises(self):
        """Test that empty output raises ValueError."""
        with pytest.raises(ValueError):
            parse_mpstat_output("")
        
        with pytest.raises(ValueError):
            parse_mpstat_output("   \n  ")

    def test_parse_no_data_lines_raises(self):
        """Test that output with no data lines raises ValueError."""
        sample_output = """
        Linux 5.15.0-46-generic (node1) 	10/25/2023 	_x86_64_	(4 CPU)
        """
        with pytest.raises(ValueError):
            parse_mpstat_output(sample_output)

    def test_aggregated_utilization_all(self):
        """Test aggregation when 'all' is present."""
        data = [
            {"cpu_id": "all", "cpu_utilization_pct": 10.0},
            {"cpu_id": "all", "cpu_utilization_pct": 20.0}
        ]
        agg = get_aggregated_utilization(data)
        assert agg["avg_utilization_pct"] == 15.0
        assert agg["max_utilization_pct"] == 20.0

    def test_aggregated_utilization_multi_core(self):
        """Test aggregation across multiple cores."""
        data = [
            {"cpu_id": "0", "cpu_utilization_pct": 10.0},
            {"cpu_id": "1", "cpu_utilization_pct": 30.0},
            {"cpu_id": "2", "cpu_utilization_pct": 20.0}
        ]
        agg = get_aggregated_utilization(data)
        # Average of 10, 30, 20
        assert agg["avg_utilization_pct"] == 20.0
        assert agg["max_utilization_pct"] == 30.0

    def test_aggregated_utilization_empty(self):
        """Test aggregation of empty list."""
        agg = get_aggregated_utilization([])
        assert agg["avg_utilization_pct"] == 0.0
        assert agg["max_utilization_pct"] == 0.0