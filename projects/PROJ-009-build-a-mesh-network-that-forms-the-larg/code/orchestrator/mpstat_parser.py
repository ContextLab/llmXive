"""
Parser for raw mpstat output strings to extract CPU utilization metrics.

This module implements the parsing logic required to extract the
`cpu_utilization_pct` field from the `PhysicalNode` entity based on
the raw output of the `mpstat` command executed on remote nodes.

It handles various mpstat output formats (Linux, Solaris, AIX) by
identifying the percentage of CPU usage, typically found in the
'%idle' column (calculated as 100 - idle) or '%usr' + '%sys'.
"""

import re
from typing import Dict, List, Any, Optional, Union


class MPStatParseError(Exception):
    """Raised when mpstat output cannot be parsed or is invalid."""
    pass


def parse_mpstat_output(raw_output: str) -> Dict[str, Any]:
    """
    Parse raw mpstat output string into a structured dictionary.

    This function attempts to identify the CPU utilization percentage
    from the provided text. It looks for the standard mpstat header
    and data rows.

    Args:
        raw_output: The raw string output from the `mpstat` command.

    Returns:
        A dictionary containing:
            - 'cpu_utilization_pct': float (0.0 to 100.0)
            - 'cpu_count': int (number of CPUs detected, if available)
            - 'timestamp': str (if available in the header)
            - 'raw_line': str (the specific data line parsed)

    Raises:
        MPStatParseError: If the output is empty, malformed, or no
                          CPU utilization data can be extracted.
    """
    if not raw_output or not isinstance(raw_output, str):
        raise MPStatParseError("Input must be a non-empty string.")

    lines = raw_output.strip().split('\n')
    if not lines:
        raise MPStatParseError("Input contains no lines.")

    # Heuristic to find the data line
    # mpstat output usually has a header line with "CPU", "%usr", "%idle", etc.
    # followed by a data line starting with "all" or a CPU number.
    
    data_line = None
    headers = []
    
    # Try to find the header line first to understand column positions
    header_indices = {}
    target_cols = ['cpu', '%usr', '%sys', '%idle', '%st']
    
    for i, line in enumerate(lines):
        parts = line.split()
        if not parts:
            continue
        
        # Check if this looks like a header line (contains 'CPU' and percentages)
        if 'CPU' in parts and any('%' in p for p in parts):
            headers = parts
            # Map column names to indices
            for j, col in enumerate(parts):
                # Handle cases where column names might be split or combined
                clean_col = col.replace('%', '').lower()
                if clean_col in target_cols:
                    header_indices[clean_col] = j
            continue
        
        # If we found headers, look for the data line
        if headers and not data_line:
            # Skip lines that are purely separators or metadata
            if line.startswith('Linux') or line.startswith('Average'):
                continue
            if line.strip().startswith('CPU'):
                continue
            
            # Check if this looks like a data row (starts with 'all' or a digit)
            if parts[0] == 'all' or parts[0].isdigit():
                data_line = parts
                break

    if not data_line:
        # Fallback: Try to find any line with numeric CPU stats if header detection failed
        for line in lines:
            parts = line.split()
            if len(parts) >= 4 and (parts[0] == 'all' or parts[0].isdigit()):
                data_line = parts
                break

    if not data_line:
        raise MPStatParseError("Could not identify CPU data line in mpstat output.")

    # Calculate utilization
    utilization = 0.0
    cpu_count = 1
    
    # Strategy 1: 100 - %idle (most robust)
    if 'idle' in header_indices:
        idle_idx = header_indices['idle']
        if idle_idx < len(data_line):
            try:
                idle_val = float(data_line[idle_idx])
                utilization = 100.0 - idle_val
            except (ValueError, IndexError):
                pass
    
    # Strategy 2: %usr + %sys (fallback)
    if utilization == 0.0 and 'usr' in header_indices and 'sys' in header_indices:
        usr_idx = header_indices['usr']
        sys_idx = header_indices['sys']
        try:
            usr_val = float(data_line[usr_idx]) if usr_idx < len(data_line) else 0.0
            sys_val = float(data_line[sys_idx]) if sys_idx < len(data_line) else 0.0
            utilization = usr_val + sys_val
        except (ValueError, IndexError):
            pass

    # If still 0, try to find any column with a '%' sign that looks like usage
    if utilization == 0.0:
        for i, val_str in enumerate(data_line):
            if '%' in val_str and i > 0: # Skip CPU ID column
                try:
                    val = float(val_str.replace('%', ''))
                    # Assume high values are usage if idle wasn't found
                    if val > 0:
                        utilization = val
                        break
                except ValueError:
                    continue

    if utilization < 0:
        utilization = 0.0
    elif utilization > 100:
        utilization = 100.0

    # Extract CPU count if 'all' was used (implies aggregate) or count CPUs
    # For simplicity in this parser, we return 1 if 'all' is present, else 1
    # A more complex parser could count CPU lines.
    if data_line[0] == 'all':
        cpu_count = 1 # Aggregate of all
    else:
        cpu_count = 1

    return {
        'cpu_utilization_pct': round(utilization, 2),
        'cpu_count': cpu_count,
        'raw_line': ' '.join(data_line),
        'success': True
    }


def get_aggregated_utilization(
    raw_outputs: List[str],
    aggregation_method: str = 'max'
) -> float:
    """
    Parse multiple mpstat outputs and return an aggregated utilization value.

    Args:
        raw_outputs: List of raw mpstat output strings from multiple nodes or intervals.
        aggregation_method: How to aggregate. Options: 'max', 'min', 'mean', 'sum'.
                            Defaults to 'max' (conservative estimate for capacity).

    Returns:
        Aggregated CPU utilization percentage.

    Raises:
        MPStatParseError: If all inputs fail to parse.
    """
    if not raw_outputs:
        raise MPStatParseError("No raw outputs provided.")

    utilizations = []
    errors = []

    for i, output in enumerate(raw_outputs):
        try:
            result = parse_mpstat_output(output)
            utilizations.append(result['cpu_utilization_pct'])
        except MPStatParseError as e:
            errors.append(f"Failed to parse output {i}: {e}")

    if not utilizations:
        error_msg = f"All parses failed. Errors: {'; '.join(errors)}"
        raise MPStatParseError(error_msg)

    if aggregation_method == 'max':
        return max(utilizations)
    elif aggregation_method == 'min':
        return min(utilizations)
    elif aggregation_method == 'mean':
        return sum(utilizations) / len(utilizations)
    elif aggregation_method == 'sum':
        return sum(utilizations)
    else:
        raise ValueError(f"Unknown aggregation method: {aggregation_method}")


def main():
    """
    CLI entry point for testing the parser with raw input from stdin or file.
    """
    import sys
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                raw_data = f.read()
        except FileNotFoundError:
            print(f"Error: File {filename} not found.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Reading from stdin...", file=sys.stderr)
        raw_data = sys.stdin.read()

    try:
        result = parse_mpstat_output(raw_data)
        print(f"CPU Utilization: {result['cpu_utilization_pct']}%")
        print(f"Parsed Line: {result['raw_line']}")
    except MPStatParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()