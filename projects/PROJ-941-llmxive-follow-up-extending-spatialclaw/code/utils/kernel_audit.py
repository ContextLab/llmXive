"""
Kernel Blockage Final Audit Script (T050).

Scans all log files in results/logs/ for instances of blocked 3D libraries
(trimesh, pytorch3d, open3d) being imported or instantiated.

Requirement: Exit with code 0 ONLY if the count of such instances is exactly 0.
Output: results/analysis/kernel_audit.txt
"""

import os
import sys
import logging
import argparse
from typing import List, Tuple, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Blocked libraries to search for
BLOCKED_LIBRARIES = {
    'trimesh',
    'pytorch3d',
    'open3d'
}

# Patterns to search for (case-insensitive logic handled in search)
SEARCH_PATTERNS = [
    'import trimesh',
    'from trimesh',
    'import pytorch3d',
    'from pytorch3d',
    'import open3d',
    'from open3d',
    # Also catch instantiation attempts if logged
    'trimesh.',
    'pytorch3d.',
    'open3d.'
]

def find_log_files(log_dir: Path) -> List[Path]:
    """Find all log files in the specified directory."""
    if not log_dir.exists():
        logger.warning(f"Log directory does not exist: {log_dir}")
        return []
    
    log_files = []
    # Search for .log and .txt files
    for ext in ['*.log', '*.txt', '*.json']:
        log_files.extend(log_dir.rglob(ext))
    
    return log_files

def scan_file_for_blocked_ops(file_path: Path) -> List[Tuple[int, str]]:
    """
    Scan a single file for blocked library usage.
    Returns a list of (line_number, line_content) for matches.
    """
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line_lower = line.lower()
                for library in BLOCKED_LIBRARIES:
                    # Check if the library name appears in a context suggesting import or usage
                    # We look for the library name preceded by import/from or followed by .
                    if f'import {library}' in line_lower or \
                       f'from {library}' in line_lower or \
                       f'{library}.' in line_lower:
                        matches.append((line_num, line.strip()))
                        break  # One match per line is enough
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
    
    return matches

def run_audit(log_dir: str, output_path: str) -> Tuple[int, List[str]]:
    """
    Run the full audit across all log files.
    Returns (total_count, list_of_violations).
    """
    log_path = Path(log_dir)
    log_files = find_log_files(log_path)
    
    all_violations = []
    total_count = 0

    if not log_files:
        logger.warning("No log files found to audit.")
        return 0, []

    logger.info(f"Scanning {len(log_files)} log files in {log_dir}...")

    for file_path in log_files:
        matches = scan_file_for_blocked_ops(file_path)
        if matches:
            logger.warning(f"Found {len(matches)} violation(s) in {file_path}")
            for line_num, content in matches:
                all_violations.append(f"{file_path}:{line_num}: {content}")
                total_count += 1
        else:
            logger.debug(f"Clean: {file_path}")

    return total_count, all_violations

def write_audit_report(output_path: str, count: int, violations: List[str]) -> None:
    """Write the audit report to the specified file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("KERNEL BLOCKAGE FINAL AUDIT REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        if count == 0:
            f.write("AUDIT PASSED: 0 blocked operations found.\n\n")
            f.write("No instances of trimesh, pytorch3d, or open3d were detected\n")
            f.write("in the execution logs.\n")
        else:
            f.write(f"AUDIT FAILED: {count} blocked operation(s) found.\n\n")
            f.write("The following violations were detected:\n")
            f.write("-" * 60 + "\n")
            for v in violations:
                f.write(f"{v}\n")
            f.write("-" * 60 + "\n")
            f.write("\nExecution of blocked 3D libraries detected. The pipeline\n")
            f.write("restriction policy may have been violated.\n")

    logger.info(f"Audit report written to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit logs for blocked 3D library usage (T050)."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="results/logs",
        help="Directory containing execution logs (default: results/logs)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/analysis/kernel_audit.txt",
        help="Path to write the audit report (default: results/analysis/kernel_audit.txt)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    count, violations = run_audit(args.log_dir, args.output)
    write_audit_report(args.output, count, violations)
    
    logger.info(f"Audit complete. Blocked operations found: {count}")
    
    # Exit with code 0 only if count is exactly 0
    if count == 0:
        logger.info("AUDIT PASSED")
        sys.exit(0)
    else:
        logger.error("AUDIT FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()