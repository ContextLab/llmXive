"""
Unit tests for mpstat_parser.py
"""
import pytest
from orchestrator.mpstat_parser import parse_mpstat_output, get_aggregated_utilization


# Mock output matching typical mpstat format
MOCK_MPSTAT_OUTPUT = """
Linux 5.15.0-76-generic (node01)  10/24/2023  _x86_64_  (4 CPU)

10:23:45 AM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:23:45 AM     all     12.50      0.00      3.25     0.50     0.00     0.10     0.00     0.00     0.00    83.65
10:23:45 AM       0     15.20      0.00      4.10     1.00     0.00     0.20     0.00     0.00     0.00    79.50
10:23:45 AM       1      9.80      0.00      2.40     0.00     0.00     0.00     0.00     0.00     0.00    87.80
"""

MOCK_MPSTAT_SINGLE_CPU = """
Linux 5.15.0-76-generic (node02)  10/24/2023  _x86_64_  (1 CPU)

10:25:00 AM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:25:00 AM       0     50.00      0.00     10.00     0.00     0.00     0.00     0.00     0.00     0.00    40.00
"""

def test_parse_mpstat_output_all_cpu():
    """Test parsing when 'all' CPU entry is present."""
    result = parse_mpstat_output(MOCK_MPSTAT_OUTPUT)
    
    assert result['cpu_id'] == 'all'
    assert result['cpu_utilization_pct'] == pytest.approx(16.35, rel=1e-4) # 100 - 83.65
    assert result['raw_stats']['idle'] == pytest.approx(83.65, rel=1e-4)
    assert result['raw_stats']['usr'] == pytest.approx(12.50, rel=1e-4)
    assert result['timestamp'] == '10:23:45 AM'

def test_parse_mpstat_output_single_cpu():
    """Test parsing when only single CPU entry is present."""
    result = parse_mpstat_output(MOCK_MPSTAT_SINGLE_CPU)
    
    assert result['cpu_id'] == '0'
    assert result['cpu_utilization_pct'] == pytest.approx(60.00, rel=1e-4) # 100 - 40.00
    assert result['raw_stats']['idle'] == pytest.approx(40.00, rel=1e-4)

def test_get_aggregated_utilization():
    """Test the helper function that returns just the float utilization."""
    util = get_aggregated_utilization(MOCK_MPSTAT_OUTPUT)
    assert util == pytest.approx(16.35, rel=1e-4)

def test_parse_empty_output():
    """Test that empty output raises ValueError."""
    with pytest.raises(ValueError, match="Empty mpstat output"):
        parse_mpstat_output("")

def test_parse_no_data_lines():
    """Test that output with only headers raises ValueError."""
    header_only = """
    Linux 5.15.0-76-generic (node01)  10/24/2023  _x86_64_  (4 CPU)
    10:23:45 AM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    """
    with pytest.raises(ValueError, match="No valid data lines found"):
        parse_mpstat_output(header_only)

def test_parse_partial_idle():
    """Test calculation when idle is 0 (100% utilization)."""
    output_100 = """
    10:00:00 AM     all     100.00      0.00      0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
    """
    result = parse_mpstat_output(output_100)
    assert result['cpu_utilization_pct'] == pytest.approx(100.0, rel=1e-4)

def test_parse_partial_idle_zero():
    """Test calculation when idle is 100 (0% utilization)."""
    output_0 = """
    10:00:00 AM     all       0.00      0.00      0.00     0.00     0.00     0.00     0.00     0.00     0.00   100.00
    """
    result = parse_mpstat_output(output_0)
    assert result['cpu_utilization_pct'] == pytest.approx(0.0, rel=1e-4)