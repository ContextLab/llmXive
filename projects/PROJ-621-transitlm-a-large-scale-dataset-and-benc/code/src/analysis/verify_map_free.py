import re
import sys
from pathlib import Path
from typing import List, Tuple
import logging
from src.lib.config import get_logger

# Regex patterns to detect geographic coordinate leakage
# Matches patterns like: lat=40.7, lon=-73.9, latitude: 40.7128, longitude: -74.0060
COORD_PATTERNS = [
    r'lat(?:itude)?[=:\s]+[-+]?\d*\.?\d+',
    r'lon(?:gitude)?[=:\s]+[-+]?\d*\.?\d+',
    r'coord[=:\s]+\([-\d\s,.]+\)',
    r'\b\d{1,2}\.\d{6,}\s*[N|S]\b', # Decimal degrees with direction
    r'\b\d{1,2}\.\d{6,}\s*[E|W]\b',
]

# Regex patterns to detect graph topology leakage (adjacency lists, edge lists)
# Matches patterns like: A -> B, (A, B), neighbors: [A, B], adjacency: {A: [B]}
TOPOLOGY_PATTERNS = [
    r'[A-Za-z0-9_]+\s*->\s*[A-Za-z0-9_]+', # Arrow notation
    r'\(\s*[A-Za-z0-9_]+\s*,\s*[A-Za-z0-9_]+\s*\)', # Tuple notation (A, B)
    r'adjacency[=:\s]*\{[^}]+\}', # Adjacency dict
    r'neighbors[=:\s]*\[[^\]]+\]', # Neighbors list
    r'edge[=:\s]*\[[^\]]+\]', # Edge list
    r'graph[=:\s]*\{[^}]+\}', # Graph structure
    r'connected_to[=:\s]+[A-Za-z0-9_\s,]+', # Connected to descriptions
]

def scan_file_for_leaks(file_path: Path, patterns: List[str]) -> List[Tuple[int, str, str]]:
    """
    Scans a file for any matches against the provided regex patterns.
    
    Args:
        file_path: Path to the file to scan.
        patterns: List of regex patterns to search for.
        
    Returns:
        List of tuples (line_number, matched_pattern, matched_text).
    """
    leaks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                for pattern in patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        leaks.append((line_num, pattern, match))
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error reading file {file_path}: {e}")
        raise
    
    return leaks

def main():
    """
    Main entry point for the map-free validation script.
    Scans the dataset files for coordinate or topology leakage.
    """
    logger = get_logger(__name__)
    logger.info("Starting map-free validation scan...")
    
    # Define the input directory containing the processed dataset
    # Based on tasks.md, the output of T014 is data/processed/train_sequences.txt
    # and test_od_pairs.json. We scan the processed directory.
    input_dir = Path("data/processed")
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist. "
                     "Please ensure T014 (dataset generation) has been run.")
        sys.exit(1)
    
    all_leaks = []
    files_scanned = 0
    
    # Scan all text and json files in the processed directory
    for file_path in input_dir.iterdir():
        if file_path.is_file() and (file_path.suffix in ['.txt', '.json', '.csv']):
            logger.info(f"Scanning {file_path}...")
            leaks = scan_file_for_leaks(file_path, COORD_PATTERNS + TOPOLOGY_PATTERNS)
            if leaks:
                all_leaks.extend(leaks)
                logger.warning(f"Found {len(leaks)} potential leaks in {file_path}")
            else:
                logger.info(f"No leaks found in {file_path}")
            files_scanned += 1
    
    if files_scanned == 0:
        logger.warning("No files found to scan in data/processed/")
        sys.exit(1)
    
    # Report results
    logger.info(f"Scan complete. Files scanned: {files_scanned}")
    
    if all_leaks:
        logger.error("VALIDATION FAILED: Geographic coordinates or graph topology detected!")
        for line_num, pattern, match in all_leaks[:10]: # Show first 10
            logger.error(f"  Line {line_num}: Matched '{pattern}' -> '{match}'")
        if len(all_leaks) > 10:
            logger.error(f"  ... and {len(all_leaks) - 10} more.")
        sys.exit(1)
    else:
        logger.info("VALIDATION PASSED: No geographic coordinates or graph topology detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()