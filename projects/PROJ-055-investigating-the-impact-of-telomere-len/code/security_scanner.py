"""
Security scanner for PROJ-055.
Scans all Python files in the code/ directory for hardcoded API keys,
secrets, or credentials.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Common patterns for API keys and secrets
# These patterns cover generic and specific services (Dryad, AnAge, etc.)
KEY_PATTERNS = [
    # Generic API key patterns
    r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-]{16,})["\']',
    r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\']([^"\']{6,})["\']',
    r'(?i)(token|auth|bearer)\s*[=:]\s*["\']([A-Za-z0-9_\-\.]{20,})["\']',
    
    # Specific service patterns
    r'(?i)(dryad[_-]?api[_-]?key|dryad[_-]?token)\s*[=:]\s*["\']([^"\']+)["\']',
    r'(?i)(anage[_-]?api[_-]?key|anage[_-]?token)\s*[=:]\s*["\']([^"\']+)["\']',
    
    # AWS-style keys
    r'(?i)(AKIA[0-9A-Z]{16})',
    
    # Generic secret assignment without env var
    r'(?i)(os\.environ|environ\[)\s*\[\s*["\']?([^"\']*(KEY|SECRET|PASSWORD|TOKEN)[^"\']*)["\']?\s*\]\s*=\s*["\']([^"\']+)["\']',
]

# Patterns that are SAFE (should not trigger warnings)
SAFE_PATTERNS = [
    # Environment variable access patterns
    r'os\.environ\.get\([^)]+\)',
    r'os\.environ\[[^]]+\]',
    r'getenv\([^)]+\)',
    # Comments about keys (not actual keys)
    r'#.*(?:API|KEY|SECRET).*',
    # Configuration loading from files
    r'load_env_config|init_config|get_config',
]

def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single file for potential hardcoded secrets.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        List of findings with location and pattern info
    """
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return findings
    
    for line_num, line in enumerate(lines, 1):
        # Skip SAFE patterns first
        is_safe = False
        for safe_pattern in SAFE_PATTERNS:
            if re.search(safe_pattern, line):
                is_safe = True
                break
        
        if is_safe:
            continue
        
        # Check against KEY patterns
        for pattern in KEY_PATTERNS:
            match = re.search(pattern, line)
            if match:
                findings.append({
                    'file': str(file_path),
                    'line': line_num,
                    'content': line.strip(),
                    'pattern': pattern,
                    'severity': 'HIGH' if 'password' in line.lower() or 'secret' in line.lower() else 'MEDIUM'
                })
                break  # Only report once per line
    
    return findings

def scan_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for hardcoded secrets in Python files.
    
    Args:
        directory: Root directory to scan
        
    Returns:
        List of all findings across all files
    """
    all_findings = []
    python_files = list(directory.rglob('*.py'))
    
    for py_file in python_files:
        # Skip test files and __pycache__
        if '__pycache__' in str(py_file):
            continue
        if 'test' in str(py_file).lower():
            continue
        
        findings = scan_file(py_file)
        all_findings.extend(findings)
    
    return all_findings

def generate_report(findings: List[Dict[str, Any]]) -> str:
    """
    Generate a human-readable security report.
    
    Args:
        findings: List of security findings
        
    Returns:
        Formatted report string
    """
    if not findings:
        return "✅ SECURITY SCAN PASSED: No hardcoded secrets detected."
    
    report_lines = [
        "❌ SECURITY SCAN FAILED: Hardcoded secrets detected!",
        "=" * 60,
        f"Total findings: {len(findings)}",
        ""
    ]
    
    # Group by severity
    high_findings = [f for f in findings if f['severity'] == 'HIGH']
    medium_findings = [f for f in findings if f['severity'] == 'MEDIUM']
    
    if high_findings:
        report_lines.append(f"HIGH SEVERITY ({len(high_findings)}):")
        for finding in high_findings:
            report_lines.append(f"  File: {finding['file']}:{finding['line']}")
            report_lines.append(f"  Content: {finding['content'][:100]}...")
            report_lines.append("")
    
    if medium_findings:
        report_lines.append(f"MEDIUM SEVERITY ({len(medium_findings)}):")
        for finding in medium_findings:
            report_lines.append(f"  File: {finding['file']}:{finding['line']}")
            report_lines.append(f"  Content: {finding['content'][:100]}...")
            report_lines.append("")
    
    report_lines.append("=" * 60)
    report_lines.append("REMEDIATION:")
    report_lines.append("  1. Remove all hardcoded keys and secrets")
    report_lines.append("  2. Use environment variables or config files")
    report_lines.append("  3. Reference keys via: os.environ.get('API_KEY_NAME')")
    report_lines.append("  4. Add .env files to .gitignore")
    
    return "\n".join(report_lines)

def main():
    """Main entry point for security scanning."""
    # Determine project root
    current_dir = Path.cwd()
    code_dir = current_dir / 'code'
    
    if not code_dir.exists():
        print(f"Error: code/ directory not found at {code_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"🔒 Scanning {code_dir} for hardcoded secrets...")
    print("-" * 60)
    
    findings = scan_directory(code_dir)
    report = generate_report(findings)
    
    print(report)
    
    if findings:
        # Write detailed findings to log
        log_path = current_dir / 'logs' / 'security_scan.log'
        log_path.parent.mkdir(exist_ok=True)
        
        with open(log_path, 'w') as f:
            f.write(f"Security scan completed at {os.popen('date').read().strip()}\n")
            f.write(f"Total findings: {len(findings)}\n\n")
            for finding in findings:
                f.write(f"File: {finding['file']}:{finding['line']}\n")
                f.write(f"Severity: {finding['severity']}\n")
                f.write(f"Content: {finding['content']}\n")
                f.write(f"Pattern: {finding['pattern']}\n\n")
        
        print(f"\nDetailed report written to: {log_path}")
        sys.exit(1)
    else:
        print("\n✅ All security checks passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()