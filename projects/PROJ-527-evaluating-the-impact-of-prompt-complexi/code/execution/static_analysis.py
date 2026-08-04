import os
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

# Security patterns to flag
SECURITY_PATTERNS = {
    "hardcoded_secret": [
        r'(?i)(api[_-]?key|secret[_-]?key|password|token|auth)[\s]*[=:][\s]*["\'][^"\']+["\']',
        r'(?i)aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][A-Z0-9]{20}["\']',
        r'(?i)private[_-]?key\s*=\s*["\'][^-]+["\']',
    ],
    "dangerous_eval": [
        r'(?i)\beval\s*\(',
        r'(?i)\bexec\s*\(',
        r'(?i)\bcompile\s*\(',
    ],
    "shell_injection": [
        r'(?i)\bos\.system\s*\(',
        r'(?i)\bsubprocess\.call\s*\([^)]*shell\s*=\s*True',
        r'(?i)\bos\.popen\s*\(',
    ],
    "insecure_random": [
        r'(?i)\brandom\.(random|randint|choice|sample)\s*\(',
    ],
}

def run_ruff_check(code: str, temp_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run ruff on the provided code string and return results."""
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp())

    code_file = temp_dir / "snippet.py"
    code_file.write_text(code)

    try:
        result = subprocess.run(
            ["ruff", "check", "--output-format=json", str(code_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return {"issues": [], "exit_code": 0}
        
        try:
            issues = json.loads(result.stdout)
            return {"issues": issues, "exit_code": 0}
        except json.JSONDecodeError:
            logger.warning("Ruff output was not valid JSON: %s", result.stdout)
            return {"issues": [], "exit_code": 0}
    except subprocess.TimeoutExpired:
        logger.error("Ruff check timed out")
        return {"issues": [], "exit_code": -1, "error": "timeout"}
    except Exception as e:
        logger.error(f"Ruff check failed: {e}")
        return {"issues": [], "exit_code": -1, "error": str(e)}

def extract_complexity_value(code: str) -> Dict[str, Any]:
    """Extract complexity metrics using ruff and regex."""
    import re
    
    # Cyclomatic complexity via ruff (C901)
    ruff_result = run_ruff_check(code)
    max_cc = 0
    for issue in ruff_result.get("issues", []):
        if issue.get("code") == "C901":
            try:
                msg = issue.get("message", "")
                match = re.search(r"(\d+)", msg)
                if match:
                    cc = int(match.group(1))
                    max_cc = max(max_cc, cc)
            except (ValueError, AttributeError):
                pass
    
    lines = code.count('\n') + 1
    return {
        "cyclomatic_complexity": max_cc,
        "lines_of_code": lines,
        "ruff_issues_count": len(ruff_result.get("issues", []))
    }

def check_security_vulnerabilities(code: str) -> List[Dict[str, Any]]:
    """
    Check code for security vulnerabilities.
    
    Returns a list of flags, each containing:
    - type: The category of vulnerability
    - pattern: The regex pattern that matched
    - line: Approximate line number (based on match index)
    - severity: 'high' or 'medium'
    
    This function does NOT fail the test; it marks samples for manual review.
    """
    flags = []
    lines = code.split('\n')
    
    for vuln_type, patterns in SECURITY_PATTERNS.items():
        for pattern in patterns:
            try:
                regex = re.compile(pattern)
                for i, line in enumerate(lines):
                    match = regex.search(line)
                    if match:
                        severity = "high" if vuln_type in ["hardcoded_secret", "dangerous_eval", "shell_injection"] else "medium"
                        flags.append({
                            "type": vuln_type,
                            "pattern": pattern,
                            "line_number": i + 1,
                            "severity": severity,
                            "snippet": line.strip()[:100]
                        })
            except re.error as e:
                logger.error(f"Invalid regex pattern for {vuln_type}: {e}")
    
    return flags

def analyze_generated_code(code: str) -> Dict[str, Any]:
    """
    Perform full static analysis on generated code.
    
    Returns a dictionary containing:
    - complexity_metrics: Cyclomatic complexity, LOC, etc.
    - security_flags: List of security vulnerability flags
    - ruff_issues: Raw ruff output
    - needs_manual_review: Boolean indicating if security flags were found
    """
    complexity_metrics = extract_complexity_value(code)
    security_flags = check_security_vulnerabilities(code)
    ruff_result = run_ruff_check(code)
    
    return {
        "complexity_metrics": complexity_metrics,
        "security_flags": security_flags,
        "ruff_issues": ruff_result.get("issues", []),
        "needs_manual_review": len(security_flags) > 0,
        "security_flag_count": len(security_flags)
    }

def main():
    """
    Main entry point for static analysis CLI.
    Expects a code string via stdin or a file path as argument.
    Outputs JSON analysis results.
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Static analysis for generated code")
    parser.add_argument("--file", type=str, help="Path to code file to analyze")
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
    else:
        code = sys.stdin.read()
    
    result = analyze_generated_code(code)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()