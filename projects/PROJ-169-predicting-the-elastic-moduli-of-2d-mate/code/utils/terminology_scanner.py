"""
Automated terminology scanner for enforcing 'Surrogate Model' vs 'First-Principles' distinction.

This script recursively scans source files and documentation (code/, docs/) for forbidden terms
that might mislabel the ML model as a first-principles solver. It outputs a JSON report
listing file paths, line numbers, and context of any violations.

Forbidden terms:
- "First-Principles" (when referring to the ML model)
- "Schrödinger" (in the context of the ML model solving it)
- "Hamiltonian" (in the context of the ML model using it directly)
- "solve equation" (when referring to the ML model)

Acceptable contexts (exempted):
- Citations or references to DFT methods (e.g., "DFT solves the Schrödinger equation")
- Historical context
- Explicit denial (e.g., "This model does NOT solve the Schrödinger equation")
"""

import os
import re
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Violation:
    """Represents a single terminology violation."""
    file_path: str
    line_number: int
    line_content: str
    term: str
    context: str
    acceptable_context: bool = False

@dataclass
class AuditReport:
    """Represents the full audit report."""
    scan_root: str
    files_scanned: int
    total_violations: int
    violations: List[Dict[str, Any]]
    scan_timestamp: str
    disclaimer: str = (
        "This report flags potential terminology violations. "
        "Manual review is required to determine if context is acceptable."
    )

# Forbidden terms (case-insensitive matching)
FORBIDDEN_PATTERNS = [
    (r'\bFirst-Principles\b', 'First-Principles'),
    (r'\bSchrödinger\b', 'Schrödinger'),
    (r'\bHamiltonian\b', 'Hamiltonian'),
    (r'\bsolve\s+equation\b', 'solve equation'),
]

# Acceptable context patterns (these exempt a match)
ACCEPTABLE_CONTEXT_PATTERNS = [
    r'does\s+NOT\s+solve',
    r'does\s+not\s+solve',
    r'NOT\s+solve',
    r'is\s+NOT\s+a\s+first-principles',
    r'is\s+not\s+a\s+first-principles',
    r'not\s+a\s+first-principles',
    r'interpolates\s+DFT',
    r'statistical\s+interpolation',
    r'surrogate\s+model',
    r'citation',
    r'reference',
    r'previous\s+work',
    r'in\s+contrast\s+to',
    r'unlike\s+DFT',
    r'compared\s+to\s+DFT',
]

def is_acceptable_context(line: str) -> bool:
    """
    Check if a line containing a forbidden term is in an acceptable context.

    Args:
        line: The line of text to check.

    Returns:
        True if the context is acceptable (e.g., denial, citation), False otherwise.
    """
    line_lower = line.lower()
    for pattern in ACCEPTABLE_CONTEXT_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            return True
    return False

def scan_file(file_path: Path, root_dir: Path) -> List[Violation]:
    """
    Scan a single file for terminology violations.

    Args:
        file_path: Path to the file to scan.
        root_dir: Root directory of the project (for relative path calculation).

    Returns:
        List of Violation objects found in the file.
    """
    violations = []
    rel_path = str(file_path.relative_to(root_dir))

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return violations

    for line_num, line in enumerate(lines, start=1):
        for pattern, term in FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if this is an acceptable context
                if is_acceptable_context(line):
                    # Log as acceptable but still note it for transparency
                    logger.debug(f"Acceptable context in {rel_path}:{line_num}: {term}")
                    continue

                violations.append(Violation(
                    file_path=rel_path,
                    line_number=line_num,
                    line_content=line.strip(),
                    term=term,
                    context=line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                ))

    return violations

def run_audit(root_dir: str, output_path: str) -> AuditReport:
    """
    Run the terminology audit on all files in the specified directory.

    Args:
        root_dir: Root directory to scan (e.g., 'code', 'docs').
        output_path: Path to write the JSON report.

    Returns:
        AuditReport object with the results.
    """
    root_path = Path(root_dir)
    all_violations: List[Violation] = []
    files_scanned = 0

    # Files to exclude
    exclude_dirs = {'data', 'results', '__pycache__', '.git', 'venv', 'env'}
    exclude_extensions = {'.pyc', '.pyo', '.so', '.dll', '.exe'}

    logger.info(f"Starting terminology audit on {root_path}")

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            # Skip excluded extensions
            if any(filename.endswith(ext) for ext in exclude_extensions):
                continue

            file_path = Path(dirpath) / filename

            # Skip data/results directories explicitly
            if 'data' in str(file_path) or 'results' in str(file_path):
                continue

            violations = scan_file(file_path, root_path)
            all_violations.extend(violations)
            files_scanned += 1

    # Generate report
    report = AuditReport(
        scan_root=str(root_path),
        files_scanned=files_scanned,
        total_violations=len(all_violations),
        violations=[asdict(v) for v in all_violations],
        scan_timestamp=str(Path(root_dir).stat().st_mtime) if root_path.exists() else "N/A"
    )

    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, indent=2)

    logger.info(f"Audit complete. Found {len(all_violations)} violations in {files_scanned} files.")
    logger.info(f"Report written to {output_path}")

    return report

def main():
    """Main entry point for the terminology scanner."""
    parser = argparse.ArgumentParser(
        description="Scan code and docs for forbidden terminology."
    )
    parser.add_argument(
        '--root',
        type=str,
        default='.',
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/terminology_audit.json',
        help='Output path for the JSON report (default: data/results/terminology_audit.json)'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run audit
    try:
        run_audit(args.root, args.output)
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        # Write a failure report
        failure_report = {
            "scan_root": args.root,
            "files_scanned": 0,
            "total_violations": 0,
            "violations": [],
            "scan_timestamp": "N/A",
            "error": str(e),
            "status": "FAILED"
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(failure_report, f, indent=2)
        raise

if __name__ == '__main__':
    main()