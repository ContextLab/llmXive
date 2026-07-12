"""
logging.py: Resource monitoring and JSON logging utilities.
"""
import json
import sys
import os
import resource
from datetime import datetime, timezone
from typing import Literal

def monitor_resources(ram_limit_gb: float = 7.0, disk_limit_gb: float = 14.0) -> dict:
    """
    Monitor current RAM and Disk usage.
    Returns a dict: {"timestamp": str, "ram_gb": float, "disk_gb": float, "status": str}
    Prints error and exits if limits are exceeded.
    """
    # Get RAM usage (maxrss is in KB on Linux/macOS, but resource.getrusage returns KB)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    ram_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB
    ram_gb = ram_mb / 1024.0

    # Get Disk usage (current directory)
    # os.statvfs returns blocks; we calculate total and used
    try:
        stat = os.statvfs(".")
        disk_total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
        disk_used_gb = ((stat.f_blocks - stat.f_bfree) * stat.f_frsize) / (1024 ** 3)
    except OSError:
        disk_total_gb = 0.0
        disk_used_gb = 0.0

    status: Literal["ok", "critical"] = "ok"
    if ram_gb > ram_limit_gb or disk_used_gb > disk_limit_gb:
        status = "critical"

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ram_gb": round(ram_gb, 3),
        "disk_gb": round(disk_used_gb, 3),
        "status": status
    }

    # Output JSON to stderr
    print(json.dumps(log_entry), file=sys.stderr)

    if status == "critical":
        print("ERROR: Resource limit exceeded", file=sys.stderr)
        sys.exit(1)

    return log_entry
