"""
Radio Metrics Collector for Mesh Network Supercomputer.

This module measures SNR (Signal-to-Noise Ratio) and bandwidth (Mbps) on remote nodes
to validate theoretical bounds (FR-006). It attempts multiple fallback methods for SNR
measurement and uses iperf3 for bandwidth measurement.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple

# Import from local orchestrator modules as per API surface
from orchestrator.logger import get_logger
from orchestrator.remote_tools_manager import RemoteToolManager, create_tool_manager

logger = get_logger(__name__)


class RadioMetricsCollectorError(Exception):
    """Base exception for radio metrics collection failures."""
    pass


class SNRMeasurementError(RadioMetricsCollectorError):
    """Raised when SNR measurement fails completely (all methods exhausted)."""
    pass


class BandwidthMeasurementError(RadioMetricsCollectorError):
    """Raised when bandwidth measurement fails."""
    pass


@dataclass
class RadioMetrics:
    """Container for radio metrics."""
    snr_db: Optional[float] = None
    bandwidth_Mbps: Optional[float] = None
    measurement_time: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    interface: str = "wlan0"
    peer_ip: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snr_db": self.snr_db,
            "bandwidth_Mbps": self.bandwidth_Mbps,
            "measurement_time": self.measurement_time,
            "interface": self.interface,
            "peer_ip": self.peer_ip
        }


def _run_local_command(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """
    Run a local command and return (returncode, stdout, stderr).
    This is used for local interface detection or fallback checks.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def _run_remote_command(ssh_client, cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
    """
    Execute a command on a remote node via SSH.
    Returns (returncode, stdout, stderr).
    """
    try:
        logger.debug(f"Executing remote command: {cmd}")
        stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=timeout)
        return_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        return return_code, out, err
    except Exception as e:
        logger.error(f"Remote command execution failed: {e}")
        return -1, "", str(e)


def _detect_primary_interface(ssh_client) -> str:
    """
    Detect the primary network interface on the remote node.
    Tries 'ip route', 'iwconfig', 'iw dev' in order.
    """
    # Try Linux 'ip route'
    rc, out, _ = _run_remote_command(ssh_client, "ip route | grep default | awk '{print $5}'")
    if rc == 0 and out.strip():
        return out.strip().split('\n')[0]

    # Fallback: try to find a wireless interface
    rc, out, _ = _run_remote_command(ssh_client, "iwconfig 2>/dev/null | grep -oE '^[^ ]+' | head -1")
    if rc == 0 and out.strip():
        return out.strip()

    # Fallback: check /proc/net/wireless
    rc, out, _ = _run_remote_command(ssh_client, "ls /sys/class/net/ | grep -E 'wlan|wifi' | head -1")
    if rc == 0 and out.strip():
        return out.strip()

    logger.warning("Could not detect primary interface, defaulting to wlan0")
    return "wlan0"


def measure_snr(ssh_client, interface: Optional[str] = None) -> Optional[float]:
    """
    Measure SNR (Signal-to-Noise Ratio) in dB.
    Implements fallback strategy:
    1. iwlist scan (Signal level - Noise level)
    2. iw dev link (signal field)
    3. /proc/net/wireless

    Returns None if all methods fail (non-critical per SC-006).
    """
    if interface is None:
        interface = _detect_primary_interface(ssh_client)

    logger.info(f"Attempting SNR measurement on interface: {interface}")

    # Method 1: iwlist scan
    logger.debug("Trying iwlist scan...")
    cmd = f"iwlist {interface} scan 2>/dev/null | grep -E 'Signal level|Noise level' | head -4"
    rc, out, err = _run_remote_command(ssh_client, cmd, timeout=15)

    if rc == 0 and out:
        try:
            lines = out.strip().split('\n')
            signal = None
            noise = None
            for line in lines:
                if 'Signal level' in line:
                    # Format: "Signal level=-45 dBm"
                    match = re.search(r'Signal level=(-?\d+)', line)
                    if match:
                        signal = int(match.group(1))
                elif 'Noise level' in line:
                    # Format: "Noise level=-90 dBm"
                    match = re.search(r'Noise level=(-?\d+)', line)
                    if match:
                        noise = int(match.group(1))

            if signal is not None and noise is not None:
                snr = signal - noise
                logger.info(f"SNR measured via iwlist: {snr} dB (Signal: {signal}, Noise: {noise})")
                return float(snr)
        except Exception as e:
            logger.warning(f"Failed to parse iwlist output: {e}")

    # Method 2: iw dev link
    logger.debug("Trying iw dev link...")
    cmd = f"iw dev {interface} link 2>/dev/null | grep signal"
    rc, out, err = _run_remote_command(ssh_client, cmd, timeout=10)

    if rc == 0 and out:
        try:
            # Format: "signal: -45.00 dBm"
            match = re.search(r'signal:\s*(-?\d+(?:\.\d+)?)', out)
            if match:
                signal = float(match.group(1))
                # Estimate noise as -90 dBm if not available (common baseline)
                # This is a heuristic; real noise varies
                noise = -90.0
                snr = signal - noise
                logger.info(f"SNR estimated via iw dev link: {snr} dB (Signal: {signal}, Noise: {noise})")
                return float(snr)
        except Exception as e:
            logger.warning(f"Failed to parse iw dev link output: {e}")

    # Method 3: /proc/net/wireless
    logger.debug("Trying /proc/net/wireless...")
    cmd = f"cat /proc/net/wireless 2>/dev/null | grep {interface}"
    rc, out, err = _run_remote_command(ssh_client, cmd, timeout=5)

    if rc == 0 and out:
        try:
            # Format: "wlan0: 0000 -45.00 -90.00 0.00 ..."
            # Columns: count, status, quality, level, noise, ...
            parts = out.split()
            if len(parts) >= 5:
                # Index 2: quality, 3: level, 4: noise (depending on kernel version)
                # Usually: level is index 3, noise is index 4
                # Values are often in dBm * 256 or similar, but modern kernels use dBm
                # Let's try direct parsing first
                level = float(parts[3])
                noise = float(parts[4])
                # If values are large (e.g. -11520), they might be scaled
                if abs(level) > 1000:
                    level = level / 256.0
                    noise = noise / 256.0
                snr = level - noise
                logger.info(f"SNR measured via /proc/net/wireless: {snr} dB")
                return float(snr)
        except Exception as e:
            logger.warning(f"Failed to parse /proc/net/wireless: {e}")

    # All methods failed
    logger.warning(f"Failed to measure SNR on {interface} after all fallback attempts. Setting to null.")
    return None


def measure_bandwidth(ssh_client, peer_ip: str, interface: Optional[str] = None, duration: int = 10) -> float:
    """
    Measure bandwidth in Mbps using iperf3.
    Runs iperf3 client on the remote node connecting to peer_ip.

    Raises BandwidthMeasurementError if measurement fails.
    """
    if interface is None:
        interface = _detect_primary_interface(ssh_client)

    logger.info(f"Measuring bandwidth to {peer_ip} via {interface} for {duration}s")

    # Ensure iperf3 is available (should be checked by T012, but verify)
    rc, _, _ = _run_remote_command(ssh_client, "which iperf3")
    if rc != 0:
        raise BandwidthMeasurementError("iperf3 not found on remote node. Ensure T012 ran successfully.")

    # Run iperf3 client
    # -c: client mode, -t: time, -J: JSON output, -i: interval (0 for summary only)
    cmd = f"iperf3 -c {peer_ip} -t {duration} -J -i 0"
    rc, out, err = _run_remote_command(ssh_client, cmd, timeout=duration + 15)

    if rc != 0:
        raise BandwidthMeasurementError(f"iperf3 failed with code {rc}: {err}")

    try:
        data = json.loads(out)
        # Extract summary bandwidth from JSON
        # Structure: {"end": {"sum": {"bits_per_second": ...}}}
        if "end" in data and "sum" in data["end"]:
            bps = data["end"]["sum"]["bits_per_second"]
            mbps = bps / 1_000_000.0
            logger.info(f"Bandwidth measured: {mbps:.2f} Mbps ({bps} bps)")
            return float(mbps)
        else:
            raise ValueError("Unexpected iperf3 JSON structure")
    except json.JSONDecodeError as e:
        raise BandwidthMeasurementError(f"Failed to parse iperf3 JSON output: {e}")
    except KeyError as e:
        raise BandwidthMeasurementError(f"Missing expected field in iperf3 output: {e}")


def collect_radio_metrics(
    ssh_client,
    peer_ip: str,
    interface: Optional[str] = None
) -> RadioMetrics:
    """
    Collect both SNR and bandwidth metrics.
    """
    metrics = RadioMetrics(interface=interface or "wlan0", peer_ip=peer_ip)

    # Measure SNR (non-critical, may return None)
    try:
        metrics.snr_db = measure_snr(ssh_client, interface)
    except Exception as e:
        logger.error(f"SNR measurement failed: {e}")
        metrics.snr_db = None

    # Measure Bandwidth (critical for FR-006)
    try:
        metrics.bandwidth_Mbps = measure_bandwidth(ssh_client, peer_ip, interface)
    except Exception as e:
        logger.error(f"Bandwidth measurement failed: {e}")
        raise BandwidthMeasurementError(f"Bandwidth measurement failed: {e}")

    return metrics


def main():
    """
    Standalone CLI for testing radio metrics collection.
    Usage: python -m orchestrator.radio_metrics_collector --ip <node_ip> --peer <peer_ip>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Collect radio metrics from a node")
    parser.add_argument("--ip", required=True, help="IP address of the target node")
    parser.add_argument("--peer", required=True, help="IP address of the iperf3 server peer")
    parser.add_argument("--interface", default=None, help="Network interface to use (default: auto-detect)")
    parser.add_argument("--duration", type=int, default=10, help="iperf3 duration in seconds")
    parser.add_argument("--user", default="root", help="SSH user")
    parser.add_argument("--key", default=None, help="Path to SSH private key")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create SSH client (simplified for CLI)
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if args.key:
            ssh.connect(args.ip, username=args.user, key_filename=args.key, timeout=10)
        else:
            ssh.connect(args.ip, username=args.user, timeout=10)
    except Exception as e:
        logger.error(f"Failed to connect to {args.ip}: {e}")
        sys.exit(1)

    try:
        metrics = collect_radio_metrics(ssh, args.peer, args.interface)
        print(json.dumps(metrics.to_dict(), indent=2))
    except BandwidthMeasurementError as e:
        logger.error(f"Critical failure: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        ssh.close()


if __name__ == "__main__":
    main()