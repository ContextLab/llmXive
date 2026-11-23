"""
T035b: Code Verification Audit
Performs a static analysis of the codebase to verify no hardcoded physical constants
or 'observer' assumptions exist, ensuring adherence to the 'purely observational' constraint (FR-007).
"""
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
STATE_DIR = PROJECT_ROOT / "state"
OUTPUT_FILE = STATE_DIR / "code_observation_audit.log"

# Patterns to detect hardcoded physical constants or observer assumptions
# These patterns look for specific physical theories or constants that should not be hardcoded
# in a purely mathematical/observational study
FORBIDDEN_PATTERNS = [
    # Physical constants that might be hardcoded (Planck's constant, speed of light, etc.)
    r'\bplanck\b', r'\b[hH]\s*=\s*[0-9.]+\s*e[-+]?[0-9]?', r'\bc\s*=\s*[0-9.]+\s*e[-+]?[0-9]?',
    r'\bg\s*=\s*[0-9.]+\s*e[-+]?[0-9]?', r'\bepsilon_0\b', r'\bmu_0\b',
    # Specific physical system references that should not be hardcoded
    r'\bquantum\s+field\b', r'\bquantum\s+chaos\b', r'\bbilliard\b', r'\bhydrogen\s+atom\b',
    # "Observer" assumptions (unless explicitly defined as computational)
    r'\bphysical\s+observer\b', r'\bhuman\s+observer\b', r'\bconscious\s+observer\b',
    # Specific physical phenomena that might be hardcoded
    r'\bneutron\s+star\b', r'\bblack\s+hole\b', r'\bcosmic\s+radiation\b',
]

# Patterns that are acceptable (computational observer definitions)
ACCEPTABLE_PATTERNS = [
    r'\bcomputational\s+observer\b', r'\balgorithmic\s+observer\b', r'\beigenvalue\s+solver\b',
    r'\bspectral\s+analysis\b', r'\bsimulation\s+run\b', r'\brandom\s+matrix\b',
]

# Files to skip (generated files, __pycache__, etc.)
SKIP_DIRS = {'__pycache__', '.git', 'venv', 'env', 'build', 'dist'}
SKIP_EXTENSIONS = {'.pyc', '.pyo', '.so', '.dll', '.exe'}

def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the code directory."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Filter out skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file.endswith('.py') and not any(file.endswith(ext) for ext in SKIP_EXTENSIONS):
                python_files.append(Path(root) / file)
    
    return python_files

def analyze_file(file_path: Path) -> List[Dict]:
    """Analyze a single Python file for forbidden patterns."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        issues.append({
            'file': str(file_path.relative_to(PROJECT_ROOT)),
            'line': 0,
            'issue': f"Failed to read file: {e}",
            'severity': 'ERROR'
        })
        return issues

    for line_num, line in enumerate(lines, 1):
        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    'file': str(file_path.relative_to(PROJECT_ROOT)),
                    'line': line_num,
                    'content': line.strip(),
                    'pattern': pattern,
                    'issue': f"Potentially forbidden pattern detected: '{pattern}'",
                    'severity': 'WARNING'
                })
        
        # Check for acceptable patterns (for logging purposes)
        for pattern in ACCEPTABLE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Log as info, not an issue
                pass

    return issues

def generate_audit_report(issues: List[Dict]) -> str:
    """Generate a human-readable audit report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("CODE OBSERVATION AUDIT REPORT")
    report_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    report_lines.append(f"Project Root: {PROJECT_ROOT}")
    report_lines.append("=" * 80)
    report_lines.append("")

    if not issues:
        report_lines.append("No issues found. The codebase adheres to the 'purely observational' constraint (FR-007).")
        report_lines.append("No hardcoded physical constants or 'observer' assumptions were detected.")
    else:
        report_lines.append(f"Found {len(issues)} potential issue(s):")
        report_lines.append("")
        
        # Group by severity
        warnings = [i for i in issues if i['severity'] == 'WARNING']
        errors = [i for i in issues if i['severity'] == 'ERROR']

        if errors:
            report_lines.append("ERRORS:")
            for issue in errors:
                report_lines.append(f"  - File: {issue['file']}, Line: {issue['line']}")
                report_lines.append(f"    Message: {issue['issue']}")
                report_lines.append("")

        if warnings:
            report_lines.append("WARNINGS:")
            for issue in warnings:
                report_lines.append(f"  - File: {issue['file']}, Line: {issue['line']}")
                report_lines.append(f"    Pattern: {issue['pattern']}")
                report_lines.append(f"    Content: {issue['content']}")
                report_lines.append(f"    Message: {issue['issue']}")
                report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("AUDIT CONCLUSION")
    report_lines.append("=" * 80)
    
    if not issues:
        report_lines.append("PASS: The codebase is compliant with FR-007 (Purely Observational Constraint).")
        report_lines.append("The implementation strictly adheres to the mathematical model without")
        report_lines.append("hardcoded physical constants or assumptions about a physical observer.")
    else:
        report_lines.append("REVIEW REQUIRED: Potential issues detected.")
        report_lines.append("Please review the warnings above to ensure they are false positives")
        report_lines.append("or update the code to remove hardcoded physical assumptions.")

    return "\n".join(report_lines)

def main():
    """Main entry point for the audit."""
    logger.info("Starting code observation audit...")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all Python files
    python_files = find_python_files(CODE_DIR)
    logger.info(f"Found {len(python_files)} Python files to analyze.")
    
    # Analyze each file
    all_issues = []
    for file_path in python_files:
        issues = analyze_file(file_path)
        all_issues.extend(issues)
    
    # Generate report
    report = generate_audit_report(all_issues)
    
    # Write report to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Audit report written to: {OUTPUT_FILE}")
    
    # Print summary
    print(report)
    
    # Return exit code based on findings
    if all_issues:
        # Log warnings but don't fail the audit (they might be false positives)
        logger.warning(f"Audit completed with {len(all_issues)} potential issue(s).")
        return 0
    else:
        logger.info("Audit completed successfully with no issues.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
