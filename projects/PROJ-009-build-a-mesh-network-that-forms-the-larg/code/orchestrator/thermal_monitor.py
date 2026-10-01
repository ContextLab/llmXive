"""
Thermal Monitor Module for Mesh Network Supercomputer.

This module implements T052: Detect thermal throttling indicators on remote nodes.
It checks for thermal zone temperatures and logs warnings if sensors are missing,
without raising errors that would halt the pipeline.
"""
from __future__ import annotations

import logging
import os
import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from orchestrator.logger import get_logger

# Constants
THERMAL_ZONE_PATH = "/sys/class/thermal/thermal_zone*/temp"
THERMAL_THROTTLING_THRESHOLD = 85000  # 85 degrees Celsius in millidegrees (Linux standard)
CRITICAL_TEMP_THRESHOLD = 95000       # 95 degrees Celsius

@dataclass
class ThermalStatus:
    """Result of thermal monitoring."""
    thermal_throttling_detected: bool
    thermal_status: str  # 'normal', 'throttled', 'unknown'
    current_temp_millidegrees: Optional[int] = None
    sensor_path: Optional[str] = None
    message: Optional[str] = None

class ThermalMonitorError(Exception):
    """Base exception for thermal monitor errors."""
    pass

def _read_local_thermal_zone(path: str) -> Optional[int]:
    """Read temperature from a local thermal zone file."""
    try:
        with open(path, 'r') as f:
            content = f.read().strip()
            # Linux thermal zones typically return millidegrees Celsius
            return int(content)
    except (IOError, ValueError, PermissionError):
        return None

def _get_local_thermal_info() -> Dict[str, Any]:
    """Get thermal information from the local machine (for testing or single-node runs)."""
    logger = get_logger(__name__)
    zones = glob.glob(THERMAL_ZONE_PATH)
    
    if not zones:
        logger.warning("No thermal zones found in /sys/class/thermal/")
        return {
            "temp_millidegrees": None,
            "sensor_path": None,
            "status": "unknown",
            "message": "thermal_sensor_missing"
        }
    
    # Read all available zones and take the highest temperature (most critical)
    max_temp = None
    max_path = None
    
    for zone in zones:
        temp = _read_local_thermal_zone(zone)
        if temp is not None:
            if max_temp is None or temp > max_temp:
                max_temp = temp
                max_path = zone
    
    if max_temp is None:
        logger.warning("Could not read any thermal zone temperatures.")
        return {
            "temp_millidegrees": None,
            "sensor_path": None,
            "status": "unknown",
            "message": "thermal_sensor_missing"
        }
    
    # Determine status
    if max_temp >= CRITICAL_TEMP_THRESHOLD:
        status = "throttled"
        throttling_detected = True
    elif max_temp >= THERMAL_THROTTLING_THRESHOLD:
        status = "throttled"
        throttling_detected = True
    else:
        status = "normal"
        throttling_detected = False
    
    return {
        "temp_millidegrees": max_temp,
        "sensor_path": max_path,
        "status": status,
        "message": None,
        "throttling_detected": throttling_detected
    }

def _execute_remote_command(ssh_client, command: str) -> tuple:
    """Execute a command on a remote node via SSH."""
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        return exit_status, output, error
    except Exception as e:
        return -1, "", str(e)

def _get_remote_thermal_info(ssh_client) -> Dict[str, Any]:
    """Get thermal information from a remote node via SSH."""
    logger = get_logger(__name__)
    
    # Try to read thermal zones
    exit_code, output, error = _execute_remote_command(
        ssh_client, 
        f"cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null || echo 'NO_SENSOR'"
    )
    
    if exit_code != 0 or "NO_SENSOR" in output or not output:
        logger.warning(f"Remote thermal sensor check failed or missing: {error}")
        return {
            "temp_millidegrees": None,
            "sensor_path": None,
            "status": "unknown",
            "message": "thermal_sensor_missing",
            "throttling_detected": False
        }
    
    # Parse output (could be multiple lines if multiple zones)
    temps = []
    for line in output.split('\n'):
        line = line.strip()
        if line.isdigit():
            temps.append(int(line))
    
    if not temps:
        logger.warning("Could not parse thermal zone temperatures from remote node.")
        return {
            "temp_millidegrees": None,
            "sensor_path": None,
            "status": "unknown",
            "message": "thermal_sensor_missing",
            "throttling_detected": False
        }
    
    # Take the highest temperature
    max_temp = max(temps)
    
    # Determine status
    if max_temp >= CRITICAL_TEMP_THRESHOLD:
        status = "throttled"
        throttling_detected = True
    elif max_temp >= THERMAL_THROTTLING_THRESHOLD:
        status = "throttled"
        throttling_detected = True
    else:
        status = "normal"
        throttling_detected = False
    
    return {
        "temp_millidegrees": max_temp,
        "sensor_path": f"/sys/class/thermal/thermal_zone_?", # Could be more specific if needed
        "status": status,
        "message": None,
        "throttling_detected": throttling_detected
    }

def check_thermal_throttling_local() -> ThermalStatus:
    """
    Check thermal throttling status on the local machine.
    
    Returns:
        ThermalStatus: Result containing throttling status and temperature info.
    """
    logger = get_logger(__name__)
    thermal_info = _get_local_thermal_info()
    
    logger.info(f"Local thermal check: status={thermal_info['status']}, temp={thermal_info['temp_millidegrees']}")
    
    return ThermalStatus(
        thermal_throttling_detected=thermal_info['throttling_detected'],
        thermal_status=thermal_info['status'],
        current_temp_millidegrees=thermal_info['temp_millidegrees'],
        sensor_path=thermal_info['sensor_path'],
        message=thermal_info['message']
    )

def check_thermal_throttling_remote(ssh_client) -> ThermalStatus:
    """
    Check thermal throttling status on a remote node via SSH.
    
    Args:
        ssh_client: Paramiko SSHClient instance connected to the remote node.
        
    Returns:
        ThermalStatus: Result containing throttling status and temperature info.
    """
    logger = get_logger(__name__)
    thermal_info = _get_remote_thermal_info(ssh_client)
    
    logger.info(f"Remote thermal check: status={thermal_info['status']}, temp={thermal_info['temp_millidegrees']}")
    
    return ThermalStatus(
        thermal_throttling_detected=thermal_info['throttling_detected'],
        thermal_status=thermal_info['status'],
        current_temp_millidegrees=thermal_info['temp_millidegrees'],
        sensor_path=thermal_info['sensor_path'],
        message=thermal_info['message']
    )

def measure_thermal_metrics(node_ip: str, ssh_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Measure thermal metrics for a node.
    
    Args:
        node_ip: IP address of the node.
        ssh_client: Optional SSH client. If None, checks local machine.
        
    Returns:
        Dict containing thermal metrics.
    """
    logger = get_logger(__name__)
    
    if ssh_client is None:
        logger.info(f"Checking thermal metrics for local machine (node: {node_ip or 'localhost'})")
        status = check_thermal_throttling_local()
    else:
        logger.info(f"Checking thermal metrics for remote node: {node_ip}")
        status = check_thermal_throttling_remote(ssh_client)
    
    return {
        "node_ip": node_ip,
        "thermal_throttling_detected": status.thermal_throttling_detected,
        "thermal_status": status.thermal_status,
        "current_temp_millidegrees": status.current_temp_millidegrees,
        "sensor_path": status.sensor_path,
        "message": status.message
    }

def main():
    """Main entry point for thermal monitoring (local testing)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Thermal Monitor for Mesh Network")
    parser.add_argument("--node-ip", type=str, default=None, help="IP of remote node (optional)")
    parser.add_argument("--ssh-key", type=str, default=None, help="Path to SSH private key")
    parser.add_argument("--ssh-user", type=str, default="root", help="SSH username")
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    logger.info("Starting thermal monitor...")
    
    if args.node_ip:
        # Remote check requires SSH
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if args.ssh_key:
                ssh.connect(args.node_ip, username=args.ssh_user, key_filename=args.ssh_key, timeout=10)
            else:
                ssh.connect(args.node_ip, username=args.ssh_user, timeout=10)
            
            result = measure_thermal_metrics(args.node_ip, ssh)
            ssh.close()
        except Exception as e:
            logger.error(f"Failed to connect to remote node {args.node_ip}: {e}")
            result = {
                "node_ip": args.node_ip,
                "thermal_throttling_detected": False,
                "thermal_status": "unknown",
                "current_temp_millidegrees": None,
                "sensor_path": None,
                "message": f"SSH connection failed: {e}"
            }
    else:
        # Local check
        result = measure_thermal_metrics("localhost")
    
    print(f"Thermal Status: {result['thermal_status']}")
    print(f"Throttling Detected: {result['thermal_throttling_detected']}")
    if result['current_temp_millidegrees'] is not None:
        print(f"Current Temperature: {result['current_temp_millidegrees'] / 1000:.1f}°C")
    if result['message']:
        print(f"Message: {result['message']}")
    
    return result

if __name__ == "__main__":
    main()
