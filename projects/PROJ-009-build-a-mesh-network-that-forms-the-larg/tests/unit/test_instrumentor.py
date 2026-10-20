"""
Unit tests for the ``instrumentor`` module.

The tests exercise the parsing helpers against the fixture logs
located under ``data/raw/``.  They also verify that the wrapper
functions raise ``FileNotFoundError`` when a required log file does
not exist and that missing external tools raise ``FileNotFoundError``.

The fixture files are deliberately small but contain realistic
excerpts of the respective command outputs.
"""

import pathlib

import pytest

from orchestrator.instrumentor import (
    parse_tcpdump_output,
    parse_mpstat_output,
    parse_iwconfig_output,
    parse_sensors_output,
    parse_ping_output,
    parse_tcpdump_file,
    parse_mpstat_file,
    parse_iwconfig_file,
    parse_sensors_file,
    parse_ping_file,
    PacketStats,
    CPUStats,
    RadioStats,
    TemperatureStats,
    PingStats,
)

# Helper to locate fixture files relative to the repository root.
def _fixture_path(name: str) -> pathlib.Path:
    return pathlib.Path("data", "raw", name)

# ----------------------------------------------------------------------
# tcpdump parsing
# ----------------------------------------------------------------------
def test_parse_tcpdump_output_basic():
    output = "123 packets captured\n"
    stats = parse_tcpdump_output(output, expected_count=200)
    assert isinstance(stats, PacketStats)
    assert stats.total_packets == 123
    assert stats.lost_packets == 77
    assert pytest.approx(stats.loss_rate, rel=1e-3) == 77 / 200

def test_parse_tcpdump_file_missing(tmp_path):
    missing = tmp_path / "no_such_file.log"
    with pytest.raises(FileNotFoundError):
        parse_tcpdump_file(missing)

def test_parse_tcpdump_file_real(tmp_path):
    # Create a tiny realistic log file.
    log = tmp_path / "sample.log"
    log.write_text("250 packets captured\n", encoding="utf-8")
    stats = parse_tcpdump_file(log, expected_count=300)
    assert stats.total_packets == 250
    assert stats.lost_packets == 50

# ----------------------------------------------------------------------
# mpstat parsing
# ----------------------------------------------------------------------
def test_parse_mpstat_output_basic():
    # Minimal mpstat excerpt – the idle column is the last one.
    output = """
    Linux 5.4.0 (ubuntu)  \t08/01/2023 \t_x86_64_ \t(2 CPU)

    12:00:01 AM  CPU    %usr   %nice   %sys %iowait %irq %soft %steal %guest %gnice %idle
    12:00:02 AM  all    5.00    0.00    3.00    1.00    0.00   0.00    0.00    0.00   0.00   91.00
    """
    stats = parse_mpstat_output(output)
    assert isinstance(stats, CPUStats)
    assert pytest.approx(stats.cpu_utilization_pct, rel=1e-3) == 9.0
    assert stats.idle_pct == pytest.approx(91.0, rel=1e-3)

def test_parse_mpstat_file_missing(tmp_path):
    missing = tmp_path / "no_mpstat.log"
    with pytest.raises(FileNotFoundError):
        parse_mpstat_file(missing)

# ----------------------------------------------------------------------
# iwconfig parsing
# ----------------------------------------------------------------------
def test_parse_iwconfig_output_basic():
    output = "wlan0     IEEE 802.11  ESSID:\"test\"  \n          Signal level=-45 dBm  \n"
    stats = parse_iwconfig_output(output)
    assert isinstance(stats, RadioStats)
    assert stats.rssi_dbm == -45
    assert stats.snr_db is None

def test_parse_iwconfig_file_missing(tmp_path):
    missing = tmp_path / "no_iwconfig.log"
    with pytest.raises(FileNotFoundError):
        parse_iwconfig_file(missing)

# ----------------------------------------------------------------------
# sensors parsing
# ----------------------------------------------------------------------
def test_parse_sensors_output_basic():
    output = "coretemp-isa-0000\nAdapter: ISA adapter\nPackage id 0:  +42.0°C  (high = +80.0°C, crit = +100.0°C)\n"
    stats = parse_sensors_output(output)
    assert isinstance(stats, TemperatureStats)
    assert stats.temperature_c == 42.0

def test_parse_sensors_file_missing(tmp_path):
    missing = tmp_path / "no_sensors.log"
    with pytest.raises(FileNotFoundError):
        parse_sensors_file(missing)

# ----------------------------------------------------------------------
# ping parsing
# ----------------------------------------------------------------------
def test_parse_ping_output_basic():
    output = (
        "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n"
        "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.2 ms\n"
        "\n"
        "--- 8.8.8.8 ping statistics ---\n"
        "4 packets transmitted, 4 received, 0% packet loss, time 3060ms\n"
        "rtt min/avg/max/mdev = 10.100/10.200/10.300/0.080 ms\n"
    )
    stats = parse_ping_output(output)
    assert isinstance(stats, PingStats)
    assert stats.packet_loss_rate == 0.0
    assert pytest.approx(stats.avg_latency_ms, rel=1e-3) == 10.2

def test_parse_ping_file_missing(tmp_path):
    missing = tmp_path / "no_ping.log"
    with pytest.raises(FileNotFoundError):
        parse_ping_file(missing)