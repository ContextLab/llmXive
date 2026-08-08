import re
from typing import Dict, List, Any, Optional, Union

def parse_mpstat_output(output: str) -> Dict[str, float]:
    """
    Parse raw mpstat output string into a dictionary of CPU metrics.
    
    Expected format (simplified):
    Linux ... time ... %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
    Average: ... %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
    
    Returns:
        Dict with keys: 'cpu_utilization_pct', 'user_pct', 'system_pct', 'idle_pct', 'iowait_pct'
    """
    lines = output.strip().split('\n')
    user_vals = []
    sys_vals = []
    idle_vals = []
    iowait_vals = []
    
    for line in lines:
        parts = line.split()
        # Skip header lines or non-data lines
        if len(parts) < 12 or parts[0] == 'Linux' or parts[0] == 'Average:':
            continue
        
        try:
            # Heuristic: assume last 4 columns are user, system, iowait, idle
            # This varies by mpstat version, so we do a best-effort parse
            # Look for numeric values in the expected range (0-100)
            nums = []
            for p in parts:
                if p.replace('.', '', 1).replace('-', '', 1).isdigit():
                    nums.append(float(p))
            
            # If we have enough numbers, try to extract
            if len(nums) >= 4:
                # Assume order: usr, sys, iowait, idle (last 4)
                user_vals.append(nums[-4])
                sys_vals.append(nums[-3])
                iowait_vals.append(nums[-2])
                idle_vals.append(nums[-1])
        except (ValueError, IndexError):
            continue
    
    if not idle_vals:
        # Fallback if parsing fails
        return {
            'cpu_utilization_pct': 0.0,
            'user_pct': 0.0,
            'system_pct': 0.0,
            'idle_pct': 100.0,
            'iowait_pct': 0.0
        }
    
    avg_user = sum(user_vals) / len(user_vals) if user_vals else 0.0
    avg_sys = sum(sys_vals) / len(sys_vals) if sys_vals else 0.0
    avg_idle = sum(idle_vals) / len(idle_vals)
    avg_iowait = sum(iowait_vals) / len(iowait_vals) if iowait_vals else 0.0
    
    utilization = 100.0 - avg_idle
    
    return {
        'cpu_utilization_pct': utilization,
        'user_pct': avg_user,
        'system_pct': avg_sys,
        'idle_pct': avg_idle,
        'iowait_pct': avg_iowait
    }

def get_aggregated_utilization(output: str) -> float:
    """
    Get aggregated CPU utilization from mpstat output.
    
    Returns:
        float: cpu_utilization_pct
    """
    metrics = parse_mpstat_output(output)
    return metrics['cpu_utilization_pct']
