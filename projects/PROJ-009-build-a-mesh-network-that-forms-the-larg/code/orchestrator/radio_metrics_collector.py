"""
Radio Metrics Collector for Mesh Network Supercomputer.

Measures SNR (Signal-to-Noise Ratio) and Bandwidth (Mbps) on remote nodes
to validate theoretical bounds (FR-006).

Specifics:
- SNR: Primary via iwlist, fallbacks via iw and /proc/net/wireless.
- Bandwidth: Via iperf3 against a peer node.
- Error Handling: If SNR cannot be measured, log WARNING and return null.
- Dependency: Requires iperf3 and iwlist/iw (ensured by T012).
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from orchestrator.logger import get_logger
from orchestrator.config import get_config

logger = get_logger(__name__)


@dataclass
class RadioMetrics:
    """Container for radio layer metrics."""
    snr_db: Optional[float] = None
    bandwidth_Mbps: Optional[float] = None
    interface: str = "wlan0"
    peer_ip: Optional[str] = None
    errors: List[str] = field(default_factory=list)

class RadioMetricsCollectorError(Exception):
    """Base exception for radio metrics collection failures."""
    pass

class BandwidthMeasurementError(RadioMetricsCollectorError):
    """Raised when bandwidth measurement fails critically."""
    pass

class SNRMeasurementError(RadioMetricsCollectorError):
    """Raised when SNR measurement fails critically (though we try to be lenient)."""
    pass


def _run_command(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """
    Execute a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Timeout expired"
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return -1, "", str(e)


def _detect_interface() -> str:
    """
    Detect the primary wireless interface.
    Tries 'iw dev' first, falls back to 'wlan0'.
    """
    # Try to get interface from 'iw dev'
    rc, out, err = _run_command(["iw", "dev"])
    if rc == 0:
        # Parse output for interface name (usually the first line after 'Interface')
        for line in out.splitlines():
            if "Interface" in line:
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
    
    # Fallback to default
    logger.warning("Could not detect wireless interface via 'iw dev', defaulting to 'wlan0'")
    return "wlan0"


def _measure_snr_iwlist(interface: str) -> Optional[float]:
    """
    Measure SNR using 'iwlist <interface> scan'.
    Calculates snr_db = signal_level - noise_level.
    """
    cmd = ["iwlist", interface, "scan"]
    rc, out, err = _run_command(cmd, timeout=60)

    if rc != 0:
        logger.debug(f"iwlist scan failed for {interface}: {err}")
        return None

    # Parse output for Signal and Noise levels
    # Typical format: Signal level=-45 dBm / Noise level=-95 dBm
    signal_match = re.search(r'Signal level=(-?\d+)\s*\w*', out)
    noise_match = re.search(r'Noise level=(-?\d+)\s*\w*', out)

    if signal_match and noise_match:
        signal = int(signal_match.group(1))
        noise = int(noise_match.group(1))
        snr = signal - noise
        logger.info(f"SNR calculated via iwlist: Signal={signal}, Noise={noise}, SNR={snr}")
        return float(snr)

    # Alternative parsing if format differs
    # Sometimes it's just "Quality=45/70  Signal level=-45 dBm"
    # We need noise for SNR. If noise is missing, we might need to estimate or fail.
    # The spec says: "Calculate snr_db = signal_level - noise_level".
    # If noise is not present, we cannot calculate exact SNR.
    
    # Check for "Quality" and "Signal" only (no noise)
    quality_match = re.search(r'Quality=(\d+)/(\d+)', out)
    signal_match_only = re.search(r'Signal level=(-?\d+)\s*\w*', out)
    
    if quality_match and signal_match_only:
        # This is a heuristic, not exact SNR. Spec asks for SNR.
        # We will return None if we can't get exact noise, to be safe, 
        # or we can log a warning and return the signal level as a proxy?
        # Spec says: "If all fail, log a WARNING and set snr_db to null".
        logger.warning(f"Could not find Noise level in iwlist output for {interface}. SNR cannot be calculated precisely.")
        return None

    return None


def _measure_snr_iw(interface: str) -> Optional[float]:
    """
    Fallback: Measure SNR using 'iw dev <interface> link'.
    Output often contains 'signal: -45 dBm'.
    Noise is harder to get here, sometimes available via 'iw dev <interface> survey dump'.
    """
    # Try 'iw dev <interface> link'
    cmd_link = ["iw", "dev", interface, "link"]
    rc, out, err = _run_command(cmd_link)

    if rc != 0:
        logger.debug(f"'iw dev {interface} link' failed: {err}")
        return None

    # Parse signal from link output
    signal_match = re.search(r'signal:\s*(-?\d+)\s*dBm', out)
    if not signal_match:
        logger.debug("Signal level not found in 'iw link' output")
        return None
    
    signal = int(signal_match.group(1))

    # Try to get noise from survey dump
    cmd_survey = ["iw", "dev", interface, "survey", "dump"]
    rc_s, out_s, err_s = _run_command(cmd_survey, timeout=10)

    noise = None
    if rc_s == 0:
        # Survey output contains "noise: -95 dBm"
        noise_match = re.search(r'noise:\s*(-?\d+)\s*dBm', out_s)
        if noise_match:
            noise = int(noise_match.group(1))
    
    if noise is not None:
        snr = signal - noise
        logger.info(f"SNR calculated via iw survey: Signal={signal}, Noise={noise}, SNR={snr}")
        return float(snr)
    else:
        logger.warning("Signal found via 'iw link', but noise not found in survey dump. Cannot calculate SNR.")
        return None


def _measure_snr_proc_wireless() -> Optional[float]:
    """
    Fallback 2: Parse /proc/net/wireless.
    This file usually contains 'noise' and 'level' (signal).
    Format: Inter-...  noise     level     ...
    """
    try:
        with open("/proc/net/wireless", "r") as f:
            lines = f.readlines()
        
        # Skip header lines
        data_lines = [l for l in lines if l.strip() and not l.startswith("Inter-")]
        
        if len(data_lines) < 2:
            return None

        # The first data line is headers, second is data (usually wlan0)
        # Actually, /proc/net/wireless has a header and then data lines.
        # Example:
        # Inter-... face ...
        # ...
        # wlan0: 0000  -45  -95 ...
        
        # We need to find the line with the interface name if multiple, 
        # but for single interface, we can just take the last non-empty line.
        data_line = data_lines[-1]
        parts = data_line.split()
        
        # Format: <iface>: <stat> <noise> <level> ...
        # The column indices vary, but typically:
        # 0: name, 1: status, 2: quality, 3: level (signal), 4: noise
        # Wait, /proc/net/wireless columns:
        # # Inter-... face ...
        # ...
        # wlan0: 0000  -95  -45 ...
        # Actually, the standard format is:
        # <iface>: <stat> <noise> <level> ... ? No.
        # Let's check standard:
        # /proc/net/wireless
        # Inter-...
        # ...
        # wlan0: 0000  -95  -45 ...
        # Columns: 
        # 1: Link Quality
        # 2: Signal level (dBm)
        # 3: Noise level (dBm)
        # Wait, man page says:
        # 1: Link Quality
        # 2: Signal Level
        # 3: Noise Level
        # But values are often negative for dBm.
        
        # Let's assume the line looks like:
        # wlan0: 0000  -45  -95 ...
        # We need to extract the two dBm values.
        # Filter for negative integers.
        nums = [int(x) for x in parts if x.lstrip('-').isdigit()]
        
        if len(nums) >= 2:
            # Usually the second is signal, third is noise? Or vice versa?
            # In iwlist: Signal level=-45, Noise level=-95.
            # In /proc/net/wireless: 
            # The columns are: Link Quality, Signal Level, Noise Level.
            # So nums[0] is Link Quality (0-70 usually), nums[1] is Signal, nums[2] is Noise.
            # But wait, the example above had -45 and -95.
            # Let's assume the two negative numbers are Signal and Noise.
            # The larger one (closer to 0) is Signal, the smaller is Noise.
            neg_nums = [n for n in nums if n < 0]
            if len(neg_nums) >= 2:
                signal = max(neg_nums) # e.g. -45
                noise = min(neg_nums)  # e.g. -95
                snr = signal - noise
                logger.info(f"SNR calculated via /proc/net/wireless: Signal={signal}, Noise={noise}, SNR={snr}")
                return float(snr)
        
        return None
    except FileNotFoundError:
        logger.warning("/proc/net/wireless not found")
        return None
    except Exception as e:
        logger.warning(f"Error parsing /proc/net/wireless: {e}")
        return None


def measure_snr(interface: str) -> Optional[float]:
    """
    Measure SNR with fallbacks.
    Returns None if all methods fail (non-critical).
    """
    # Primary: iwlist
    snr = _measure_snr_iwlist(interface)
    if snr is not None:
        return snr

    # Fallback 1: iw
    snr = _measure_snr_iw(interface)
    if snr is not None:
        return snr

    # Fallback 2: /proc/net/wireless
    snr = _measure_snr_proc_wireless()
    if snr is not None:
        return snr

    logger.warning("All SNR measurement methods failed. Returning null.")
    return None


def measure_bandwidth(peer_ip: str, interface: str = "wlan0", duration: int = 10) -> Optional[float]:
    """
    Measure bandwidth using iperf3.
    Returns None if measurement fails.
    """
    if not peer_ip:
        logger.warning("No peer IP provided for bandwidth measurement.")
        return None

    # iperf3 command: iperf3 -c <peer> -t <duration> -J
    # -J outputs JSON
    cmd = ["iperf3", "-c", peer_ip, "-t", str(duration), "-J", "-i", "0"]
    rc, out, err = _run_command(cmd, timeout=duration + 30)

    if rc != 0:
        logger.error(f"iperf3 failed: {err}")
        return None

    try:
        data = json.loads(out)
        # Structure: {"end": {"sum": {"bits_per_second": ...}}}
        if "end" in data and "sum" in data["end"]:
            bps = data["end"]["sum"]["bits_per_second"]
            mbps = bps / 1_000_000.0
            logger.info(f"Bandwidth measured: {mbps:.2f} Mbps")
            return mbps
        else:
            logger.warning("iperf3 JSON output missing expected fields.")
            return None
    except json.JSONDecodeError:
        logger.error(f"Failed to parse iperf3 output: {out}")
        return None


def collect_radio_metrics(interface: Optional[str] = None, peer_ip: Optional[str] = None) -> RadioMetrics:
    """
    Main entry point to collect radio metrics.
    """
    if interface is None:
        interface = _detect_interface()
    
    metrics = RadioMetrics(interface=interface, peer_ip=peer_ip)

    # Measure SNR
    snr = measure_snr(interface)
    metrics.snr_db = snr

    # Measure Bandwidth
    if peer_ip:
        bw = measure_bandwidth(peer_ip, interface)
        metrics.bandwidth_Mbps = bw
    else:
        logger.warning("No peer IP provided, skipping bandwidth measurement.")
        metrics.bandwidth_Mbps = None

    return metrics


def main():
    """
    CLI entry point for testing radio metrics collection.
    Usage: python -m orchestrator.radio_metrics_collector --peer <IP>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Collect radio metrics (SNR, Bandwidth)")
    parser.add_argument("--peer", type=str, required=False, help="Peer IP for iperf3")
    parser.add_argument("--interface", type=str, required=False, help="Network interface (default: auto-detect)")
    args = parser.parse_args()

    logger.info("Starting radio metrics collection...")
    metrics = collect_radio_metrics(interface=args.interface, peer_ip=args.peer)
    
    print(json.dumps({
        "snr_db": metrics.snr_db,
        "bandwidth_Mbps": metrics.bandwidth_Mbps,
        "interface": metrics.interface,
        "peer_ip": metrics.peer_ip,
        "errors": metrics.errors
    }, indent=2))

    if metrics.snr_db is None and metrics.bandwidth_Mbps is None:
        logger.error("No metrics collected.")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()