"""
mpstat_parser.py

Parses raw mpstat output strings into structured CPU utilization metrics.
Extracts `cpu_utilization_pct` for the PhysicalNode entity.
"""
import re
from typing import Dict, List, Any, Optional, Union


def parse_mpstat_output(output: str) -> Dict[str, Any]:
    """
    Parses a raw mpstat command output string.
    
    Expected format (example):
    Linux 5.15.0-76-generic (node01)  10/24/2023  _x86_64_  (4 CPU)
    
    10:23:45 AM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    10:23:45 AM     all     12.50      0.00      3.25     0.50     0.00     0.10     0.00     0.00     0.00    83.65
    10:23:45 AM       0     15.20      0.00      4.10     1.00     0.00     0.20     0.00     0.00     0.00    79.50
    10:23:45 AM       1      9.80      0.00      2.40     0.00     0.00     0.00     0.00     0.00     0.00    87.80
    
    Returns a dictionary with:
      - 'timestamp': str (parsed from output if available)
      - 'cpu_id': str (e.g., 'all', '0', '1')
      - 'cpu_utilization_pct': float (100 - %idle)
      - 'raw_stats': dict (all parsed percentages)
    
    Raises:
        ValueError: If the output cannot be parsed or no data lines are found.
    """
    lines = output.strip().split('\n')
    if not lines:
        raise ValueError("Empty mpstat output provided.")
    
    result = {
        'timestamp': None,
        'cpu_id': None,
        'cpu_utilization_pct': None,
        'raw_stats': {}
    }
    
    # Regex to match data lines
    # Format: HH:MM:SS AM/PM  CPU  %usr ... %idle
    # We look for lines that start with a time or contain 'all' / digits for CPU
    data_pattern = re.compile(
        r'^(?P<time>\d{2}:\d{2}:\d{2}\s+(?:AM|PM))?\s*'
        r'(?P<cpu>all|\d+)\s+'
        r'(?P<usr>[\d.]+)\s+'
        r'(?P<nice>[\d.]+)\s+'
        r'(?P<sys>[\d.]+)\s+'
        r'(?P<iowait>[\d.]+)\s+'
        r'(?P<irq>[\d.]+)\s+'
        r'(?P<soft>[\d.]+)\s+'
        r'(?P<steal>[\d.]+)\s+'
        r'(?P<guest>[\d.]+)\s+'
        r'(?P<gnice>[\d.]+)\s+'
        r'(?P<idle>[\d.]+)\s*$'
    )
    
    parsed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if line.startswith('Linux') or line.startswith('Average') or line.startswith('CPU'):
            continue
        
        match = data_pattern.match(line)
        if match:
            groups = match.groupdict()
            
            # Parse idle percentage
            try:
                idle_pct = float(groups['idle'])
            except (ValueError, TypeError):
                continue
            
            # Calculate utilization: 100 - idle
            utilization = 100.0 - idle_pct
            
            parsed_entry = {
                'timestamp': groups['time'],
                'cpu_id': groups['cpu'],
                'cpu_utilization_pct': utilization,
                'raw_stats': {
                    'usr': float(groups['usr']),
                    'nice': float(groups['nice']),
                    'sys': float(groups['sys']),
                    'iowait': float(groups['iowait']),
                    'irq': float(groups['irq']),
                    'soft': float(groups['soft']),
                    'steal': float(groups['steal']),
                    'guest': float(groups['guest']),
                    'gnice': float(groups['gnice']),
                    'idle': idle_pct,
                }
            }
            parsed_lines.append(parsed_entry)
    
    if not parsed_lines:
        raise ValueError("No valid data lines found in mpstat output.")
    
    # If 'all' is present, prioritize it as the aggregate metric for the node
    all_entry = next((entry for entry in parsed_lines if entry['cpu_id'] == 'all'), None)
    if all_entry:
        return all_entry
    
    # Otherwise, return the first entry (assuming single CPU or first available)
    return parsed_lines[0]


def get_aggregated_utilization(output: str) -> float:
    """
    Parses mpstat output and returns the aggregated CPU utilization percentage.
    Prioritizes the 'all' CPU entry if available.
    
    Args:
        output: Raw mpstat output string.
    
    Returns:
        float: The CPU utilization percentage (0.0 to 100.0).
    
    Raises:
        ValueError: If parsing fails or no valid data is found.
    """
    parsed = parse_mpstat_output(output)
    if parsed['cpu_utilization_pct'] is None:
        raise ValueError("Could not determine CPU utilization from output.")
    return parsed['cpu_utilization_pct']
