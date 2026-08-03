"""
Parser for raw mpstat output strings into structured CPU utilization data.
"""
import re
from typing import Dict, List, Any

def parse_mpstat_output(raw_output: str) -> List[Dict[str, Any]]:
    """
    Parse raw mpstat output into a list of dictionaries containing
    CPU utilization percentages per core.
    """
    if not raw_output or "raw_mpstat_output" in raw_output:
        return []

    # Regex to match mpstat lines (simplified)
    # Format: CPU    %usr   %nice   %sys   %iowait   %irq   %soft   %steal   %guest   %gnice   %idle
    pattern = re.compile(r'^\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)')
    
    results = []
    lines = raw_output.strip().split('\n')
    
    for line in lines:
        match = pattern.match(line)
        if match:
            cpu_id = match.group(1)
            if cpu_id == 'Average':
                continue
            results.append({
                'cpu': cpu_id,
                'usr_pct': float(match.group(2)),
                'sys_pct': float(match.group(4)),
                'idle_pct': float(match.group(11)),
                'utilization_pct': 100.0 - float(match.group(11))
            })
    
    return results
