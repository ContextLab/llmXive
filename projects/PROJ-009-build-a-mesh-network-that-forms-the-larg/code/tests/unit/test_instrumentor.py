import pathlib
from orchestrator.instrumentor import (
    parse_tcpdump_file,
    parse_mpstat_file,
    parse_iwconfig_file,
    parse_sensors_file,
    parse_ping_file,
    compute_packet_loss_rate,
    PacketStats,
)

def test_parse_tcpdump_output():
    """Parse a tcpdump log fixture and verify packet statistics."""
    log_path = pathlib.Path("data/raw/sample_tcpdump.log")
    stats = parse_tcpdump_file(log_path, expected_count=200)
    assert isinstance(stats, PacketStats)
    assert stats.total_packets == 123
    # Expected loss rate = (expected - captured) / expected
    assert stats.loss_rate == (200 - 123) / 200

def test_parse_mpstat_output():
    """Parse an mpstat log fixture and verify CPU utilisation fields."""
    log_path = pathlib.Path("data/raw/sample_mpstat.log")
    stats = parse_mpstat_file(log_path)
    # Utilisation should be a realistic percentage between 0 and 100
    assert 0.0 <= stats.cpu_utilization_pct <= 100.0
    # The parser always provides a numeric value for user/system percentages
    assert isinstance(stats.user_pct, float)
    assert isinstance(stats.system_pct, float)

def test_parse_iwconfig_output():
    """Parse an iwconfig log fixture and verify RSSI and SNR extraction."""
    log_path = pathlib.Path("data/raw/sample_iwconfig.log")
    stats = parse_iwconfig_file(log_path)
    assert stats.rssi_dbm == -40
    assert stats.snr_db == 50.0

def test_parse_sensors_output():
    """Parse a sensors log fixture and verify temperature extraction."""
    log_path = pathlib.Path("data/raw/sample_sensors.log")
    stats = parse_sensors_file(log_path)
    # The fixture contains a temperature of +42.0°C
    assert stats.temperature_c == 42.0

def test_parse_ping_output():
    """Parse a ping log fixture and verify latency and loss parsing."""
    log_path = pathlib.Path("data/raw/sample_ping.log")
    stats = parse_ping_file(log_path)
    # Average latency in the fixture is 0.030 ms
    assert stats.avg_latency_ms == 0.030
    # No packet loss in the fixture
    assert stats.packet_loss_rate == 0.0

def test_compute_packet_loss_rate():
    """The convenience wrapper should simply return the loss_rate field."""
    ps = PacketStats(
        total_packets=100,
        packets_per_second=100.0,
        lost_packets=0,
        loss_rate=0.0,
    )
    assert compute_packet_loss_rate(ps) == 0.0
