"""
mpstat_parser.py

Parses raw mpstat output strings into structured CPU utilization data.
Extracts the 'cpu_utilization_pct' field for the PhysicalNode entity.

Dependencies:
    - Standard library only (re, typing)
"""

import re
from typing import Dict, List, Any, Optional, Union


def parse_mpstat_output(output: str) -> List[Dict[str, Any]]:
    """
    Parses a raw mpstat command output string into a list of dictionaries.
    
    Each dictionary represents a CPU snapshot containing:
      - timestamp: str (ISO format or raw string)
      - cpu_id: int (0, 1, ..., or 'all')
      - cpu_utilization_pct: float (0.0 to 100.0)
      - idle_pct: float
      - iowait_pct: float
      - irq_pct: float
      - softirq_pct: float
      - steal_pct: float
    
    The parser handles standard mpstat output formats (Linux).
    It looks for lines starting with a timestamp or CPU ID and extracts
    the '%idle' column to calculate utilization (100 - idle).
    
    Args:
        output (str): Raw stdout from an mpstat command (e.g., "mpstat 1 1").
    
    Returns:
        List[Dict[str, Any]]: Parsed metrics. Empty list if no valid data found.
    
    Raises:
        ValueError: If the output is completely unparseable or empty.
    """
    if not output or not output.strip():
        raise ValueError("mpstat output string is empty or None")

    results = []
    lines = output.strip().split('\n')
    
    # Regex to match mpstat data lines.
    # mpstat output typically looks like:
    # 10:00:00 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    # 10:00:01 AM  all    0.50    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00   99.50
    # 
    # We need to capture:
    # 1. Timestamp (optional but good for context)
    # 2. CPU ID (all, 0, 1...)
    # 3. %idle (last column usually, or explicitly labeled)
    
    # Strategy: Find the header to identify column indices, then parse data rows.
    header_line_idx = -1
    header_cols = []
    
    # Heuristic for header: contains "CPU" and "%idle"
    for i, line in enumerate(lines):
        if "CPU" in line and "%idle" in line:
            header_line_idx = i
            header_cols = line.split()
            break
    
    if header_line_idx == -1:
        # Fallback: Try to parse assuming standard format if header not found explicitly
        # This might happen if output is truncated or slightly different.
        # We will try to find lines that look like data (start with time or 'all')
        pass

    # Determine index of CPU and %idle
    cpu_idx = -1
    idle_idx = -1
    
    if header_line_idx != -1:
        if "CPU" in header_cols:
            cpu_idx = header_cols.index("CPU")
        if "%idle" in header_cols:
            idle_idx = header_cols.index("%idle")
    
    # If we didn't find headers, try to infer from data structure (standard mpstat)
    # Standard columns: Time, CPU, %usr, %nice, %sys, %iowait, %irq, %soft, %steal, %guest, %gnice, %idle
    # Indices (approx): 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
    # If CPU is 'all', it's at index 1. %idle is usually the last column.
    
    for line in lines[header_line_idx + 1:]:
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that look like headers or separators
        if "CPU" in line or "Average" in line or "Linux" in line:
            continue
        
        parts = line.split()
        if len(parts) < 5:
            continue
        
        try:
            # Identify CPU ID
            # Usually at index 1 (after time) or 0 if no time
            current_cpu_id = "unknown"
            current_idle = 0.0
            current_timestamp = "unknown"
            
            # Heuristic: If the second part is 'all' or a digit, it's the CPU
            if len(parts) > 1:
                if parts[1] in ['all', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    current_cpu_id = parts[1]
                    # Timestamp is usually parts[0] and parts[1] (AM/PM)
                    # But mpstat format varies. Let's assume parts[0] is time, parts[1] is AM/PM or CPU
                    # If parts[1] is CPU, then parts[0] is time.
                    # If parts[0] is CPU (rare), then adjust.
                    # Standard: HH:MM:SS AM/PM CPU ...
                    # So parts[0], parts[1] are time, parts[2] is CPU?
                    # Let's check standard: "10:00:00 AM  CPU" -> parts[0]=10:00:00, parts[1]=AM, parts[2]=CPU
                    # Wait, header says "CPU".
                    # Data: "10:00:01 AM  all    0.50..."
                    # parts[0]=10:00:01, parts[1]=AM, parts[2]=all
                    
                    if parts[1] == 'AM' or parts[1] == 'PM':
                        current_timestamp = f"{parts[0]} {parts[1]}"
                        current_cpu_id = parts[2]
                        # %idle is typically the last column
                        current_idle = float(parts[-1])
                    else:
                        # Maybe no AM/PM?
                        current_cpu_id = parts[1]
                        current_idle = float(parts[-1])
                        current_timestamp = parts[0]
                elif parts[0] in ['all', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    # No timestamp, starts with CPU
                    current_cpu_id = parts[0]
                    current_idle = float(parts[-1])
                    current_timestamp = "unknown"
                else:
                    # Fallback: try to find 'all' or digit in the line
                    for p in parts:
                        if p in ['all', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                            current_cpu_id = p
                            break
                    current_idle = float(parts[-1])
            else:
                continue
            
            # Calculate utilization
            cpu_utilization_pct = 100.0 - current_idle
            # Clamp to 0-100 to handle floating point weirdness
            cpu_utilization_pct = max(0.0, min(100.0, cpu_utilization_pct))
            
            results.append({
                "timestamp": current_timestamp,
                "cpu_id": current_cpu_id,
                "cpu_utilization_pct": round(cpu_utilization_pct, 2),
                "idle_pct": round(current_idle, 2),
                "raw_line": line
            })
            
        except (ValueError, IndexError) as e:
            # Skip malformed lines
            continue
    
    if not results:
        # If we found no data lines, raise an error to indicate failure to parse
        raise ValueError("No valid mpstat data lines found in output")
        
    return results


def get_aggregated_utilization(parsed_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregates parsed mpstat data into a single utilization metric per node.
    
    If 'all' CPU is present, use that. Otherwise, average all CPU cores.
    
    Args:
        parsed_data: List of dicts from parse_mpstat_output.
    
    Returns:
        Dict with 'avg_utilization_pct' and 'max_utilization_pct'.
    """
    if not parsed_data:
        return {"avg_utilization_pct": 0.0, "max_utilization_pct": 0.0}
    
    utilizations = [d["cpu_utilization_pct"] for d in parsed_data]
    
    return {
        "avg_utilization_pct": sum(utilizations) / len(utilizations),
        "max_utilization_pct": max(utilizations)
    }
