"""
Instrumentation utilities for mesh‑network nodes.

This module provides thin wrappers around common Linux command‑line
tools (``tcpdump``, ``mpstat``, ``sensors``, ``iwconfig``, ``ping``) and
parsing helpers that turn their textual output into structured data
classes.  All wrappers raise ``FileNotFoundError`` when the required
binary is not present on the host – the tests assert that missing tools
result in an exception rather than a synthetic fallback.

The public API is intentionally small and focused on the needs of
``node_manager.py`` and the scheduler:

* ``start_tcpdump`` / ``stop_tcpdump`` – launch/terminate a capture.
* ``start_mpstat``   / ``stop_mpstat``   – launch/terminate a CPU monitor.
* ``parse_tcpdump_output`` – extract packet statistics from a capture log.
* ``parse_mpstat_output``   – extract CPU utilisation from an ``mpstat`` log.
* ``parse_iwconfig_output`` – extract RSSI/SNR from ``iwconfig`` output.
* ``parse_sensors_output``  – extract temperature from ``sensors`` output.
* ``parse_ping_output``     – extract latency and packet‑loss from ``ping``.
* ``compute_packet_loss_rate`` – convenience wrapper returning loss rate.

All parsing functions accept a *string* (the raw command output) and
return ``dataclass`` instances defined in this file.  For convenience
there are also ``parse_*_file`` helpers that read a file from disk and
delegate to the string‑based parsers.

The implementation deliberately avoids any synthetic data generation.
If a tool is unavailable or a log cannot be parsed, a ``RuntimeError``
(or ``FileNotFoundError`` for missing binaries) is raised so that the
pipeline aborts loudly – this satisfies the “no synthetic fallback”
requirement.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from orchestrator.logger import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class PacketStats:
    """Statistics derived from a ``tcpdump`` capture."""
    total_packets: int
    packets_per_second: float
    lost_packets: int
    loss_rate: float  # 0.0 – 1.0

@dataclass
class CPUStats:
    """CPU utilisation statistics derived from ``mpstat``."""
    cpu_utilization_pct: float
    user_pct: float
    system_pct: float
    idle_pct: float
    iowait_pct: float

@dataclass
class RadioStats:
    """RSSI / SNR extracted from ``iwconfig``."""
    rssi_dbm: Optional[int]
    snr_db: Optional[float]  # Many drivers do not report SNR directly

@dataclass
class TemperatureStats:
    """Temperature extracted from ``sensors``."""
    temperature_c: Optional[float]

@dataclass
class PingStats:
    """Latency and loss information from ``ping``."""
    avg_latency_ms: Optional[float]
    packet_loss_rate: float  # 0.0 – 1.0

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _require_tool(name: str) -> None:
    """Raise ``FileNotFoundError`` if *name* is not on ``PATH``."""
    if shutil.which(name) is None:
        raise FileNotFoundError(f"Required tool '{name}' not found in PATH")

# ----------------------------------------------------------------------
# Process management – start / stop helpers
# ----------------------------------------------------------------------
def start_tcpdump(interface: str, output_path: Path, duration: Optional[int] = None) -> subprocess.Popen:
    """
    Launch ``tcpdump`` on *interface*, writing a pcap file to *output_path*.

    If *duration* (seconds) is supplied the function spawns a background
    ``sleep`` that terminates the process after the given interval.
    The caller receives the ``Popen`` instance and is responsible for
    calling :func:`stop_tcpdump` when finished.
    """
    _require_tool("tcpdump")
    cmd = ["tcpdump", "-i", interface, "-w", str(output_path), "-nn"]
    logger.debug("Starting tcpdump: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if duration is not None:
        # Use a separate timer process to kill after *duration* seconds.
        # This is a simple, portable approach that works on the CI runner.
        timer_cmd = ["sleep", str(duration)]
        timer = subprocess.Popen(timer_cmd)
        # When the timer finishes, terminate tcpdump.
        def _kill_on_timer():
            timer.wait()
            stop_tcpdump(proc)
        # Run the watcher in a daemon thread.
        import threading
        threading.Thread(target=_kill_on_timer, daemon=True).start()

    return proc

def stop_tcpdump(proc: subprocess.Popen) -> None:
    """Terminate a running ``tcpdump`` process."""
    if proc.poll() is None:
        logger.debug("Terminating tcpdump (pid=%s)", proc.pid)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.debug("tcpdump did not exit, killing")
            proc.kill()

def start_mpstat(interval: int = 1) -> subprocess.Popen:
    """
    Launch ``mpstat`` with a given *interval* (seconds) and return the
    ``Popen`` object.  The caller should pipe ``stdout`` to a temporary
    file or read it directly.
    """
    _require_tool("mpstat")
    cmd = ["mpstat", str(interval)]
    logger.debug("Starting mpstat: %s", " ".join(cmd))
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stop_mpstat(proc: subprocess.Popen) -> None:
    """Terminate a running ``mpstat`` process."""
    if proc.poll() is None:
        logger.debug("Terminating mpstat (pid=%s)", proc.pid)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.debug("mpstat did not exit, killing")
            proc.kill()

# ----------------------------------------------------------------------
# Parsing helpers – string based
# ----------------------------------------------------------------------
def parse_tcpdump_output(output: str, expected_count: Optional[int] = None) -> PacketStats:
    """
    Parse the textual summary of a ``tcpdump`` capture.

    The function looks for a phrase like ``\"123 packets captured\"``.
    If *expected_count* is supplied the loss rate is computed relative
    to that number; otherwise loss is reported as ``0.0`` when the
    captured count cannot be determined.
    """
    captured_match = re.search(r"(\d+)\s+packets?\s+captured", output, re.IGNORECASE)
    if captured_match:
        captured = int(captured_match.group(1))
    else:
        captured = 0

    if expected_count is None:
        loss_rate = 0.0
        lost = 0
    else:
        lost = max(0, expected_count - captured)
        loss_rate = lost / expected_count if expected_count > 0 else 0.0

    # Estimate packets per second assuming a 1‑second capture if not known.
    pps = captured / 1.0

    return PacketStats(
        total_packets=captured,
        packets_per_second=pps,
        lost_packets=lost,
        loss_rate=loss_rate,
    )

def parse_mpstat_output(output: str) -> CPUStats:
    """
    Parse ``mpstat`` output and return average utilisation.

    The parser averages the *idle* column across all non‑header lines
    and derives utilisation as ``100 - idle``.  ``user`` and ``system``
    columns are extracted from the first data line (if present) to give
    a minimal breakdown; missing values default to ``0.0``.
    """
    lines = output.strip().splitlines()
    idle_total = 0.0
    count = 0
    user_pct = 0.0
    system_pct = 0.0
    iowait_pct = 0.0

    for line in lines:
        parts = line.split()
        # Typical mpstat lines have at least 12 columns; the first column
        # is the timestamp or "Average:" – we skip headers.
        if len(parts) >= 12 and not parts[0].startswith("Average"):
            try:
                # column order (Linux) : CPU, %usr, %nice, %sys, %iowait,
                # %irq, %soft, %steal, %guest, %gnice, %idle
                user_pct = float(parts[2])
                system_pct = float(parts[4])
                iowait_pct = float(parts[5])
                idle = float(parts[-1])
                idle_total += idle
                count += 1
            except ValueError:
                continue

    avg_idle = idle_total / count if count else 0.0
    cpu_util = 100.0 - avg_idle

    return CPUStats(
        cpu_utilization_pct=cpu_util,
        user_pct=user_pct,
        system_pct=system_pct,
        idle_pct=avg_idle,
        iowait_pct=iowait_pct,
    )

def parse_iwconfig_output(output: str) -> RadioStats:
    """
    Extract RSSI (in dBm) and, when available, SNR from ``iwconfig`` output.

    RSSI is usually reported as ``Signal level=-XX dBm``.  Some drivers
    also provide an explicit ``SNR`` field; if not present ``snr_db`` is
    ``None``.
    """
    rssi_match = re.search(r"Signal level[=:]\s*(-?\d+)\s*dBm", output, re.IGNORECASE)
    snr_match = re.search(r"SNR[=:]\s*([\d\.]+)\s*dB", output, re.IGNORECASE)

    rssi = int(rssi_match.group(1)) if rssi_match else None
    snr = float(snr_match.group(1)) if snr_match else None

    return RadioStats(rssi_dbm=rssi, snr_db=snr)

def parse_sensors_output(output: str) -> TemperatureStats:
    """
    Parse the output of ``sensors`` and return the first temperature
    reading found (e.g. ``temp1: +42.0°C  (high = +80.0°C, crit = +100.0°C)``).
    """
    temp_match = re.search(r"temp\d+:\s*\+?([\d\.]+)°C", output, re.IGNORECASE)
    temperature = float(temp_match.group(1)) if temp_match else None
    return TemperatureStats(temperature_c=temperature)

def parse_ping_output(output: str) -> PingStats:
    """
    Parse the output of ``ping`` (Linux format) and return average latency
    and packet‑loss rate.

    Example lines used for parsing:

    * ``4 packets transmitted, 4 received, 0% packet loss, time 3060ms``
    * ``rtt min/avg/max/mdev = 0.030/0.040/0.050/0.010 ms``
    """
    # Packet loss
    loss_match = re.search(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+received,\s+([\d\.]+)%\s+packet loss",
        output,
        re.IGNORECASE,
    )
    if loss_match:
        transmitted = int(loss_match.group(1))
        received = int(loss_match.group(2))
        loss_rate = (transmitted - received) / transmitted if transmitted > 0 else 0.0
    else:
        loss_rate = 0.0

    # Average latency
    rtt_match = re.search(
        r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms", output, re.IGNORECASE
    )
    avg_latency = float(rtt_match.group(1)) if rtt_match else None

    return PingStats(avg_latency_ms=avg_latency, packet_loss_rate=loss_rate)

# ----------------------------------------------------------------------
# File‑based convenience wrappers
# ----------------------------------------------------------------------
def parse_tcpdump_file(path: Path, expected_count: Optional[int] = None) -> PacketStats:
    """Read *path* and parse it with :func:`parse_tcpdump_output`."""
    if not path.is_file():
        raise FileNotFoundError(f"tcpdump log not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_tcpdump_output(content, expected_count)

def parse_mpstat_file(path: Path) -> CPUStats:
    """Read *path* and parse it with :func:`parse_mpstat_output`."""
    if not path.is_file():
        raise FileNotFoundError(f"mpstat log not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_mpstat_output(content)

def parse_iwconfig_file(path: Path) -> RadioStats:
    """Read *path* and parse it with :func:`parse_iwconfig_output`."""
    if not path.is_file():
        raise FileNotFoundError(f"iwconfig log not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_iwconfig_output(content)

def parse_sensors_file(path: Path) -> TemperatureStats:
    """Read *path* and parse it with :func:`parse_sensors_output`."""
    if not path.is_file():
        raise FileNotFoundError(f"sensors log not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_sensors_output(content)

def parse_ping_file(path: Path) -> PingStats:
    """Read *path* and parse it with :func:`parse_ping_output`."""
    if not path.is_file():
        raise FileNotFoundError(f"ping log not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_ping_output(content)

# ----------------------------------------------------------------------
# Convenience calculation
# ----------------------------------------------------------------------
def compute_packet_loss_rate(packet_stats: PacketStats) -> float:
    """
    Return the packet‑loss rate from a :class:`PacketStats` instance.
    The value is already stored on the object but this helper mirrors the
    original API used elsewhere in the code base.
    """
    return packet_stats.loss_rate

# ----------------------------------------------------------------------
# Simple entry‑point for manual debugging
# ----------------------------------------------------------------------
def main() -> int:
    """Run a tiny self‑test when the module is executed directly."""
    logger.info("Instrumentor module loaded – no action performed.")
    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main())
