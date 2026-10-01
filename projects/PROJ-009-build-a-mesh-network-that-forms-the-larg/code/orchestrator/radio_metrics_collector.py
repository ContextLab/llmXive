"""
Radio Metrics Collector for Mesh Network Supercomputer.

Measures Signal-to-Noise Ratio (SNR) and Bandwidth for theoretical bound validation.
Implements strict fallback logic and fails loudly on critical bandwidth failures.
"""
from __future__ import annotations

import logging
import re
import subprocess
import sys
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.remote_tools_manager import RemoteToolManager, create_tool_manager, ToolMissingError, RemoteExecutionError

logger = get_logger(__name__)


class RadioMetricsCollectorError(Exception):
    """Base exception for radio metrics collection failures."""
    pass


class SNRMeasurementError(RadioMetricsCollectorError):
    """Raised when SNR measurement fails completely (all fallbacks exhausted)."""
    pass


class BandwidthMeasurementError(RadioMetricsCollectorError):
    """Raised when bandwidth measurement fails (critical for theoretical bounds)."""
    pass


@dataclass
class RadioMetrics:
    """Container for radio metric measurements."""
    snr_db: Optional[float]
    bandwidth_Mbps: float
    measurement_method: str
    interface: str
    peer_ip: Optional[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _run_ssh_command(ssh_client, command: str, timeout: int = 30) -> str:
    """Execute a command on the remote node via SSH."""
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='replace')
        error_output = stderr.read().decode('utf-8', errors='replace')
        
        if exit_status != 0:
            logger.warning(f"Command failed with exit code {exit_status}: {command}")
            logger.debug(f"Error output: {error_output}")
            raise RemoteExecutionError(f"Command failed: {command} (exit {exit_status})")
        
        return output
    except Exception as e:
        raise RemoteExecutionError(f"SSH execution failed: {str(e)}")


def measure_snr(ssh_client, interface: str = "wlan0") -> Optional[float]:
    """
    Measure Signal-to-Noise Ratio (SNR) using multiple fallback strategies.
    
    Strategy 1: iwlist scan
    Strategy 2: iw dev link
    Strategy 3: /proc/net/wireless
    
    Returns None if all methods fail (non-critical per SC-006).
    """
    methods_tried = []
    
    # Method 1: iwlist
    try:
        logger.info(f"Attempting SNR measurement via iwlist on {interface}")
        cmd = f"iwlist {interface} scan | grep -E 'Signal level|Noise level'"
        output = _run_ssh_command(ssh_client, cmd)
        
        signal_match = re.search(r'Signal level=(-?\d+)dBm', output)
        noise_match = re.search(r'Noise level=(-?\d+)dBm', output)
        
        if signal_match and noise_match:
            signal = float(signal_match.group(1))
            noise = float(noise_match.group(2))
            snr = signal - noise
            logger.info(f"SNR measured via iwlist: {snr:.2f} dB (Signal: {signal}, Noise: {noise})")
            return snr
        else:
            methods_tried.append("iwlist (no match)")
    except Exception as e:
        logger.warning(f"iwlist failed: {str(e)}")
        methods_tried.append(f"iwlist: {str(e)}")

    # Method 2: iw
    try:
        logger.info(f"Attempting SNR measurement via iw on {interface}")
        cmd = f"iw dev {interface} link | grep signal"
        output = _run_ssh_command(ssh_client, cmd)
        
        signal_match = re.search(r'signal:\s*(-?\d+)\s*dBm', output)
        if signal_match:
            signal = float(signal_match.group(1))
            # Estimate noise as -90dBm if not available (common default)
            noise = -90.0
            snr = signal - noise
            logger.info(f"SNR estimated via iw: {snr:.2f} dB (Signal: {signal}, Noise: {noise})")
            return snr
        else:
            methods_tried.append("iw (no match)")
    except Exception as e:
        logger.warning(f"iw failed: {str(e)}")
        methods_tried.append(f"iw: {str(e)}")

    # Method 3: /proc/net/wireless
    try:
        logger.info(f"Attempting SNR measurement via /proc/net/wireless")
        cmd = "cat /proc/net/wireless"
        output = _run_ssh_command(ssh_client, cmd)
        
        # Format: Inter-   st   tx-   rx-   tx-   rx-   tx-   rx-   tx-   rx-   tx-   rx-   tx-   rx-
        #           face   at   err   err   drop  drop  over  mod   crc   frame  bytes   bytes   bytes   bytes
        #           wlan0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
        # Line 3 contains the data for wlan0 (assuming first interface)
        lines = [l.strip() for l in output.split('\n') if l.strip() and not l.startswith('Inter')]
        if len(lines) >= 1:
            # Parse the line - columns are typically: 
            # quality, level, noise, etc.
            # Format varies by kernel, often: link quality, signal level, noise level, etc.
            parts = lines[0].split()
            if len(parts) >= 3:
                # Assuming format: iface qual level noise ...
                # Values are often in 0-100 or dBm format depending on driver
                # For iw, values are typically dBm for level and noise
                # Let's try to interpret as dBm if negative, or scale if positive
                try:
                    # If the values look like dBm (negative numbers)
                    signal = float(parts[1]) if float(parts[1]) < 0 else float(parts[1]) - 100
                    noise = float(parts[2]) if float(parts[2]) < 0 else float(parts[2]) - 100
                    snr = signal - noise
                    logger.info(f"SNR estimated via /proc/net/wireless: {snr:.2f} dB")
                    return snr
                except (ValueError, IndexError):
                    pass
        methods_tried.append("/proc/net/wireless (parse failed)")
    except Exception as e:
        logger.warning(f"/proc/net/wireless failed: {str(e)}")
        methods_tried.append(f"/proc/net/wireless: {str(e)}")

    logger.warning(f"All SNR measurement methods failed: {methods_tried}")
    return None


def measure_bandwidth(ssh_client, peer_ip: str, interface: str = "wlan0", duration: int = 5) -> float:
    """
    Measure bandwidth using iperf3.
    
    This is a critical measurement for theoretical bound validation (FR-006).
    Raises BandwidthMeasurementError if iperf3 is missing or fails.
    """
    # Ensure iperf3 is available (T012 should have handled this, but double-check)
    try:
        _run_ssh_command(ssh_client, "which iperf3")
    except RemoteExecutionError:
        raise BandwidthMeasurementError("iperf3 not found on remote node. Ensure T012 tool verification passed.")

    try:
        logger.info(f"Starting bandwidth measurement to {peer_ip} on {interface} for {duration}s")
        
        # Run iperf3 as client, JSON output
        # -c: client mode, -t: time, -J: JSON output, -i: interval (0 for summary only)
        cmd = f"iperf3 -c {peer_ip} -t {duration} -J -i 0"
        output = _run_ssh_command(ssh_client, cmd, timeout=duration + 10)
        
        # Parse JSON output
        try:
            data = json.loads(output)
            # Extract sum of all intervals or just the summary
            if 'end' in data and 'sum_sent' in data['end']:
                # Get bits per second from summary
                bits_per_second = data['end']['sum_sent']['bits_per_second']
                mbps = bits_per_second / 1_000_000.0
                logger.info(f"Bandwidth measured: {mbps:.2f} Mbps")
                return mbps
            elif 'intervals' in data and len(data['intervals']) > 0:
                # Sum up all intervals
                total_bits = 0
                for interval in data['intervals']:
                    total_bits += interval['sum']['bits_per_second']
                avg_mbps = (total_bits / len(data['intervals'])) / 1_000_000.0
                logger.info(f"Average bandwidth measured: {avg_mbps:.2f} Mbps")
                return avg_mbps
            else:
                raise ValueError("Unexpected iperf3 JSON structure")
        except json.JSONDecodeError as e:
            raise BandwidthMeasurementError(f"Failed to parse iperf3 JSON output: {str(e)}")
        
    except RemoteExecutionError as e:
        raise BandwidthMeasurementError(f"iperf3 execution failed: {str(e)}")
    except Exception as e:
        raise BandwidthMeasurementError(f"Bandwidth measurement failed: {str(e)}")


def collect_radio_metrics(
    ssh_client,
    peer_ip: str,
    interface: str = "wlan0"
) -> RadioMetrics:
    """
    Main entry point to collect all radio metrics for a node.
    
    Args:
        ssh_client: Paramiko SSHClient instance
        peer_ip: IP address of the peer node for bandwidth test
        interface: Network interface to measure (default: wlan0)
        
    Returns:
        RadioMetrics object with measured values.
    """
    errors = []
    snr = None
    bandwidth = None
    method = "none"

    # Measure SNR (non-critical, can be null)
    try:
        snr = measure_snr(ssh_client, interface)
        if snr is not None:
            method = "snr_primary"
    except SNRMeasurementError as e:
        errors.append(f"SNR error: {str(e)}")
    except Exception as e:
        errors.append(f"SNR unexpected error: {str(e)}")

    # Measure Bandwidth (critical)
    try:
        bandwidth = measure_bandwidth(ssh_client, peer_ip, interface)
        if bandwidth is not None:
            if snr is None:
                method = "bandwidth_only"
            else:
                method = "complete"
    except BandwidthMeasurementError as e:
        errors.append(f"Bandwidth error: {str(e)}")
        # Re-raise as it's critical for theoretical bounds
        raise e
    except Exception as e:
        errors.append(f"Bandwidth unexpected error: {str(e)}")
        raise BandwidthMeasurementError(f"Bandwidth measurement failed: {str(e)}")

    if snr is None and bandwidth is None:
        raise RadioMetricsCollectorError("Both SNR and bandwidth measurements failed.")

    return RadioMetrics(
        snr_db=snr,
        bandwidth_Mbps=bandwidth,
        measurement_method=method,
        interface=interface,
        peer_ip=peer_ip,
        errors=errors
    )


def main():
    """
    CLI entry point for testing radio metrics collection.
    
    Usage:
        python -m orchestrator.radio_metrics_collector --ip 192.168.1.10 --peer 192.168.1.11
    """
    import argparse
    from orchestrator.node_manager import create_node_manager

    parser = argparse.ArgumentParser(description="Collect radio metrics from a mesh node")
    parser.add_argument("--ip", required=True, help="IP address of the target node")
    parser.add_argument("--peer", required=True, help="IP address of the peer node for bandwidth test")
    parser.add_argument("--interface", default="wlan0", help="Network interface to measure")
    parser.add_argument("--config", default="config/testbed.yaml", help="Path to testbed config")
    
    args = parser.parse_args()

    # Load config
    try:
        from orchestrator.config import get_config
        config = get_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        sys.exit(1)

    # Connect to node
    try:
        node_manager = create_node_manager(config)
        # For this test, we assume single node connection
        ssh_client = node_manager.connect(args.ip)
        
        if ssh_client:
            logger.info(f"Connected to {args.ip}")
            metrics = collect_radio_metrics(ssh_client, args.peer, args.interface)
            print(json.dumps(metrics.to_dict(), indent=2))
            ssh_client.close()
        else:
            logger.error(f"Failed to connect to {args.ip}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Radio metrics collection failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()