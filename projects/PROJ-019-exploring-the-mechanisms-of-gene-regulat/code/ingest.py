"""
Ingestion module for parsing BED files.
Handles downloading and initial parsing of ENCODE peak data.
"""
import logging
from typing import List, Tuple, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class BedParseError(ValueError):
    """Custom exception for BED parsing errors."""
    pass

def parse_bed_line(line: str) -> Tuple[str, int, int, str]:
    """
    Parse a single BED line into (chrom, start, end, name).
    
    Args:
        line: A single line from a BED file.
        
    Returns:
        Tuple of (chrom, start, end, name).
        
    Raises:
        ValueError: If the line is malformed (missing required columns).
        BedParseError: If coordinates are invalid or non-integer.
    """
    parts = line.strip().split('\t')
    
    if len(parts) < 3:
        msg = f"Malformed BED line: expected at least 3 columns, got {len(parts)}. Line: {line}"
        logger.error(msg)
        raise ValueError(msg)
    
    chrom = parts[0]
    try:
        start = int(parts[1])
        end = int(parts[2])
    except ValueError:
        msg = f"Malformed BED line: start/end must be integers. Line: {line}"
        logger.error(msg)
        raise ValueError(msg)
    
    if start < 0:
        msg = f"Malformed BED line: start coordinate cannot be negative. Line: {line}"
        logger.error(msg)
        raise ValueError(msg)
        
    if end <= start:
        msg = f"Malformed BED line: end must be greater than start. Line: {line}"
        logger.error(msg)
        raise ValueError(msg)
    
    name = parts[3] if len(parts) > 3 else f"{chrom}:{start}-{end}"
    
    return chrom, start, end, name

def parse_bed_file(file_path: str) -> List[Tuple[str, int, int, str]]:
    """
    Parse a BED file into a list of peak records.
    
    Args:
        file_path: Path to the BED file.
        
    Returns:
        List of tuples (chrom, start, end, name).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If any line is malformed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    peaks = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('track') or line.startswith('browser'):
                continue
            
            try:
                peak = parse_bed_line(line)
                peaks.append(peak)
            except ValueError as e:
                logger.error(f"Error parsing line {line_num}: {e}")
                raise
                
    return peaks
