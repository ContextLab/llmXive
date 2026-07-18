"""
Terminology Scanner for Surrogate Model Compliance.

This script recursively scans source files and documentation for forbidden terms
that misrepresent the ML model as "First-Principles" physics.

Forbidden terms:
- "First-Principles" (when referring to the ML model)
- "Schrödinger" (when implying the model solves it)
- "Hamiltonian" (when implying the model calculates from it)
- "solve equation" (in the context of physics solving)

Output: JSON report to data/results/terminology_audit.json
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

# Forbidden terms and patterns
# We look for these terms in the context of the ML model's capabilities
FORBIDDEN_PATTERNS = [
    r'\bFirst-Principles\b',
    r'\bFirst Principles\b',
    r'\bFirstPrinciples\b',
    r'\bSchrödinger\b',
    r'\bSchrodinger\b',  # ASCII fallback
    r'\bHamiltonian\b',
    r'\bsolve\s+the\s+equation\b',
    r'\bsolve\s+equations?\b',
    r'\bsolving\s+the\s+equation\b',
    r'\bsolving\s+equations?\b',
]

# Contexts where terms might be acceptable (e.g., citations, historical context)
# These are patterns that indicate the term is being discussed, not claimed
ACCEPTABLE_CONTEXTS = [
    r'cited?\s+as',
    r'referring\s+to',
    r'compared\s+to',
    r'unlike\s+',
    r'does\s+not\s+(?:solve|calculate)',
    r'not\s+(?:solving|calculating)',
    r'in\s+contrast\s+to',
    r'whereas',
    r'where',
    r'while',
    r'although',
    r'however',
    r'but',
    r'note\s+that',
    r'warning:',
    r'limitation',
    r' caveat',
]

@dataclass
class Violation:
    """Represents a single terminology violation."""
    file_path: str
    line_number: int
    line_content: str
    pattern_matched: str
    context: str

@dataclass
class AuditReport:
    """Represents the complete audit report."""
    scan_timestamp: str
    total_files_scanned: int
    total_violations: int
    violations: List[Dict[str, Any]]
    summary: Dict[str, int]

def is_acceptable_context(line: str, match_start: int, match_end: int) -> bool:
    """
    Check if a match occurs in an acceptable context (e.g., citation, negation).
    
    Args:
        line: The full line of text
        match_start: Start index of the matched pattern
        match_end: End index of the matched pattern
        
    Returns:
        True if the context is acceptable (term is being discussed, not claimed)
    """
    # Get surrounding context (100 chars before and after)
    start = max(0, match_start - 100)
    end = min(len(line), match_end + 100)
    context = line[start:end]
    
    # Check if any acceptable context pattern matches
    for pattern in ACCEPTABLE_CONTEXTS:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    
    return False

def scan_file(file_path: Path, project_root: Path) -> List[Violation]:
    """
    Scan a single file for forbidden terminology.
    
    Args:
        file_path: Path to the file to scan
        project_root: Root of the project (for relative paths)
        
    Returns:
        List of Violation objects found in the file
    """
    violations = []
    relative_path = str(file_path.relative_to(project_root))
    
    try:
        # Skip binary files
        if file_path.suffix in ['.pyc', '.so', '.bin', '.parquet', '.png', '.jpg', '.gif']:
            return violations
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern in FORBIDDEN_PATTERNS:
                matches = list(re.finditer(pattern, line, re.IGNORECASE))
                for match in matches:
                    # Check if this is an acceptable context
                    if not is_acceptable_context(line, match.start(), match.end()):
                        violation = Violation(
                            file_path=relative_path,
                            line_number=line_num,
                            line_content=line.strip(),
                            pattern_matched=pattern,
                            context=line[max(0, match.start()-50):min(len(line), match.end()+50)]
                        )
                        violations.append(violation)
    except Exception as e:
        logger.warning(f"Error scanning file {file_path}: {e}")
        
    return violations

def run_audit(project_root: Path, output_path: Path) -> AuditReport:
    """
    Run the full terminology audit on the project.
    
    Args:
        project_root: Root of the project
        output_path: Path to write the JSON report
        
    Returns:
        AuditReport object with all findings
    """
    import datetime
    
    all_violations: List[Violation] = []
    files_scanned = 0
    
    # Directories to scan
    scan_dirs = [
        project_root / 'code',
        project_root / 'docs',
    ]
    
    # Directories to exclude
    exclude_dirs = [
        project_root / 'data',
        project_root / 'state',
        project_root / '__pycache__',
    ]
    
    logger.info(f"Starting terminology audit on {project_root}")
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            logger.warning(f"Scan directory does not exist: {scan_dir}")
            continue
            
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file():
                # Check if file is in an excluded directory
                is_excluded = False
                for exclude_dir in exclude_dirs:
                    if exclude_dir in file_path.parents or file_path.parent == exclude_dir:
                        is_excluded = True
                        break
                
                if is_excluded:
                    continue
                    
                violations = scan_file(file_path, project_root)
                if violations:
                    all_violations.extend(violations)
                    files_scanned += 1
                    
    # Build summary
    summary = {
        'First-Principles': 0,
        'Schrödinger': 0,
        'Hamiltonian': 0,
        'solve equation': 0,
    }
    
    for v in all_violations:
        if 'First-Principles' in v.pattern_matched or 'First Principles' in v.pattern_matched:
            summary['First-Principles'] += 1
        elif 'Schrödinger' in v.pattern_matched or 'Schrodinger' in v.pattern_matched:
            summary['Schrödinger'] += 1
        elif 'Hamiltonian' in v.pattern_matched:
            summary['Hamiltonian'] += 1
        elif 'solve' in v.pattern_matched.lower():
            summary['solve equation'] += 1
            
    report = AuditReport(
        scan_timestamp=datetime.datetime.now().isoformat(),
        total_files_scanned=files_scanned,
        total_violations=len(all_violations),
        violations=[asdict(v) for v in all_violations],
        summary=summary
    )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, indent=2)
        
    logger.info(f"Audit complete. Found {len(all_violations)} violations.")
    logger.info(f"Report written to {output_path}")
    
    return report

def main():
    """Main entry point for the terminology scanner."""
    parser = argparse.ArgumentParser(
        description='Scan project for forbidden terminology'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path('.'),
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output path for the JSON report (default: data/results/terminology_audit.json)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = args.project_root.resolve()
    if args.output:
        output_path = args.output.resolve()
    else:
        output_path = project_root / 'data' / 'results' / 'terminology_audit.json'
        
    # Run audit
    report = run_audit(project_root, output_path)
    
    # Exit with code 1 if violations found (for CI/CD integration)
    if report.total_violations > 0:
        logger.error(f"Found {report.total_violations} terminology violations!")
        for v in report.violations[:5]:  # Show first 5
            logger.error(f"  {v['file_path']}:{v['line_number']} - {v['pattern_matched']}")
        if report.total_violations > 5:
            logger.error(f"  ... and {report.total_violations - 5} more")
        return 1
    else:
        logger.info("No terminology violations found. Compliance check passed.")
        return 0

if __name__ == '__main__':
    exit(main())
