import os
import sys
import logging
import argparse
import re
from typing import List, Tuple, Set
from pathlib import Path

# Blocked libraries that must NOT appear in logs
BLOCKED_LIBRARIES = {"trimesh", "pytorch3d", "open3d"}

def find_log_files(logs_dir: str = "results/logs") -> List[Path]:
    """Find all log files in the specified directory, including subdirectories."""
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        logging.warning(f"Logs directory {logs_dir} does not exist.")
        return []
    
    log_files = []
    
    # Check root of logs_dir
    for ext in ["*.log", "*.txt", "*.json", "*.jsonl"]:
        log_files.extend(logs_path.glob(ext))
    
    # Check subdirectories recursively
    for subdir in logs_path.rglob("*"):
        if subdir.is_dir():
            for ext in ["*.log", "*.txt", "*.json", "*.jsonl"]:
                log_files.extend(subdir.glob(ext))
    
    # Remove duplicates and return as list
    return list(set(log_files))

def scan_file_for_blocked_ops(file_path: Path) -> List[Tuple[str, str]]:
    """Scan a single file for blocked library imports or instantiations.
    
    Returns a list of (library, line_content) tuples for any matches found.
    """
    found_ops = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                for lib in BLOCKED_LIBRARIES:
                    # Check for import statements or module usage
                    # Patterns: "import trimesh", "from trimesh import", "import trimesh as", "trimesh."
                    if re.search(rf'\b{re.escape(lib)}\b', line_lower):
                        found_ops.append((lib, f"Line {line_num}: {line.strip()}"))
    except Exception as e:
        logging.error(f"Error scanning {file_path}: {e}")
    
    return found_ops

def run_audit(logs_dir: str = "results/logs") -> Tuple[int, List[Tuple[Path, List[Tuple[str, str]]]]]:
    """Run the full audit across all log files.
    
    Returns:
        Tuple of (total_blocked_count, findings) where findings is a list of
        (file_path, [(lib, line_content), ...]) tuples.
    """
    log_files = find_log_files(logs_dir)
    total_blocked_count = 0
    findings = []
    
    if not log_files:
        logging.warning(f"No log files found in {logs_dir}")
        return 0, []
    
    for log_file in log_files:
        found = scan_file_for_blocked_ops(log_file)
        if found:
            findings.append((log_file, found))
            total_blocked_count += len(found)
            for lib, line_content in found:
                logging.warning(f"Found blocked op '{lib}' in {log_file}: {line_content}")
    
    return total_blocked_count, findings

def write_audit_report(report_path: str, total_count: int, findings: List[Tuple[Path, List[Tuple[str, str]]]]) -> None:
    """Write the audit report to the specified file."""
    report_dir = os.path.dirname(report_path)
    if report_dir and not os.path.exists(report_dir):
        os.makedirs(report_dir, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("Kernel Blockage Final Audit Report\n")
        f.write("=" * 50 + "\n\n")
        
        if total_count == 0:
            f.write("AUDIT PASSED: 0 blocked operations found.\n\n")
            f.write("The following log files were scanned:\n")
            scanned_files = find_log_files()
            if scanned_files:
                for log_file in sorted(scanned_files):
                    f.write(f"  - {log_file}\n")
            else:
                f.write("  (No log files found in the specified directory)\n")
        else:
            f.write(f"AUDIT FAILED: {total_count} blocked operations found.\n\n")
            f.write("Findings:\n")
            for file_path, ops in findings:
                f.write(f"  File: {file_path}\n")
                for lib, line_content in ops:
                    f.write(f"    [{lib}] {line_content}\n")
        
        f.write("\nAudit completed.\n")
    
    logging.info(f"Audit report written to {report_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit logs for blocked 3D library usage.")
    parser.add_argument("--logs-dir", type=str, default="results/logs",
                      help="Directory containing log files to scan")
    parser.add_argument("--output", type=str, default="results/analysis/kernel_audit.txt",
                      help="Output path for the audit report")
    return parser.parse_args()

def main() -> int:
    """Main entry point for the kernel audit."""
    args = parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info(f"Starting kernel audit on {args.logs_dir}")
    
    total_count, findings = run_audit(args.logs_dir)
    write_audit_report(args.output, total_count, findings)
    
    if total_count == 0:
        logging.info("Audit passed successfully.")
        return 0
    else:
        logging.error(f"Audit failed with {total_count} violations.")
        return 1

if __name__ == "__main__":
    sys.exit(main())