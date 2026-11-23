import logging
from typing import List, Tuple, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class BedParseError(Exception):
    """Raised when a BED line cannot be parsed correctly."""
    pass

def parse_bed_line(line: str) -> Tuple[str, int, int, str]:
    """
    Parse a single BED line into (chrom, start, end, name).
    BED format is 0-based, start inclusive, end exclusive.
    """
    parts = line.strip().split('\t')
    if len(parts) < 4:
        raise BedParseError(f"Invalid BED line (less than 4 columns): {line}")

    chrom = parts[0]
    try:
        start = int(parts[1])
        end = int(parts[2])
    except ValueError:
        raise BedParseError(f"Invalid BED coordinates: {line}")

    if start < 0 or end < start:
        raise BedParseError(f"Invalid BED coordinates (start >= end or negative): {line}")

    name = parts[3] if len(parts) > 3 else "."
    return chrom, start, end, name

def parse_bed_file(file_path: Path) -> List[Tuple[str, int, int, str]]:
    """
    Parse a BED file and return a list of tuples.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"BED file not found: {file_path}")

    records = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip() or line.startswith('track') or line.startswith('browser'):
                continue
            try:
                record = parse_bed_line(line)
                records.append(record)
            except BedParseError as e:
                logger.warning(f"Skipping malformed line {line_num} in {file_path}: {e}")

    return records
