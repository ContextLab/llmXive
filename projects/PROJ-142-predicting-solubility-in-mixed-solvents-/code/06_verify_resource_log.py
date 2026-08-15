"""
Verification script for the resource monitor log.

This script implements Task T026c: Resource Monitor (Verify).
It reads data/artifacts/resource_monitor.log, validates its structure,
and checks for critical flags (timeout, resource_exceeded).

Usage:
    python code/06_verify_resource_log.py [--log-path <path>]

Exit Codes:
    0: Log is valid and contains expected entries.
    1: Log is missing, empty, or contains critical errors (resource exceeded/timeout).
"""
import os
import sys
import json
import argparse
from pathlib import Path
from utils.constants import DATA_DIR

def verify_log_integrity(log_path: Path) -> dict:
    """
    Verify the integrity and content of the resource monitor log.
    
    Args:
        log_path: Path to the resource_monitor.log file.
        
    Returns:
        A dictionary containing verification results:
        - status: 'valid', 'critical', or 'error'
        - entries_count: Number of log entries found
        - has_timeout: Boolean indicating if 'timeout' flag was found
        - has_resource_exceeded: Boolean indicating if 'resource_exceeded' flag was found
        - messages: List of log messages (last 10)
    """
    result = {
        "status": "error",
        "entries_count": 0,
        "has_timeout": False,
        "has_resource_exceeded": False,
        "messages": [],
        "error_message": None
    }

    if not log_path.exists():
        result["error_message"] = f"Log file not found: {log_path}"
        return result

    if log_path.stat().st_size == 0:
        result["error_message"] = "Log file is empty"
        return result

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        result["error_message"] = f"Failed to read log file: {str(e)}"
        return result

    valid_entries = 0
    timeout_found = False
    exceeded_found = False
    recent_messages = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            valid_entries += 1
            
            # Check for critical flags in the entry
            if entry.get("status") == "critical":
                msg = entry.get("message", "")
                if "timeout" in msg.lower():
                    timeout_found = True
                if "resource" in msg.lower() and "exceed" in msg.lower():
                    exceeded_found = True
            
            # Also check for explicit flags if present
            if entry.get("flag") == "timeout":
                timeout_found = True
            if entry.get("flag") == "resource_exceeded":
                exceeded_found = True
                
            recent_messages.append(line)
            if len(recent_messages) > 10:
                recent_messages.pop(0)
                
        except json.JSONDecodeError:
            # Skip malformed lines but continue processing
            continue

    result["entries_count"] = valid_entries
    result["has_timeout"] = timeout_found
    result["has_resource_exceeded"] = exceeded_found
    result["messages"] = recent_messages

    if valid_entries == 0:
        result["error_message"] = "No valid JSON entries found in log"
        return result

    # Determine overall status
    if exceeded_found or timeout_found:
        result["status"] = "critical"
    else:
        result["status"] = "valid"

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Verify the resource monitor log integrity and content."
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        help="Path to the resource monitor log. Defaults to data/artifacts/resource_monitor.log"
    )
    
    args = parser.parse_args()
    
    # Determine log path
    if args.log_path:
        log_path = Path(args.log_path)
    else:
        log_path = DATA_DIR / "artifacts" / "resource_monitor.log"
        
    print(f"Verifying log file: {log_path}")
    
    verification_result = verify_log_integrity(log_path)
    
    print(f"Status: {verification_result['status']}")
    print(f"Valid Entries: {verification_result['entries_count']}")
    
    if verification_result['error_message']:
        print(f"Error: {verification_result['error_message']}")
        sys.exit(1)
        
    if verification_result['has_timeout']:
        print("Flag Detected: TIMEOUT")
        
    if verification_result['has_resource_exceeded']:
        print("Flag Detected: RESOURCE_EXCEEDED")
        
    if verification_result['status'] == "critical":
        print("WARNING: Critical resource limits were hit or process was terminated.")
        # Exit 1 to indicate a critical event was detected in the log
        sys.exit(1)
        
    print("Verification successful: Log file is valid and contains expected entries.")
    sys.exit(0)

if __name__ == "__main__":
    main()
