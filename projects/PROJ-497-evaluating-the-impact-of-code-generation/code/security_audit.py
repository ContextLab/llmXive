"""
Security Hardening: PII Leakage Detection for Logs and Reports.

This module scans all generated logs, reports, and data artifacts within the project
to detect potential Personally Identifiable Information (PII) leakage.

It checks for:
- Standard PII patterns (Email, Phone, SSN, Credit Card, IP addresses)
- Git user metadata (Name/Email) in commit logs or code comments
- API keys or secrets in configuration or generated code
- Human-readable names in code comments or docstrings (if they look like PII)

Usage:
    python code/security_audit.py
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

# Configure logging to stdout (no file logging to avoid creating PII in logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Define PII regex patterns based on common standards
PII_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone_us": re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
    "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
    "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "aws_access_key": re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    "github_token": re.compile(r'\bghp_[0-9a-zA-Z]{36}\b'),
    "slack_token": re.compile(r'\bxox[baprs]-[0-9a-zA-Z]{10,48}\b'),
    "git_user_name": re.compile(r'\b(?:User|Author|Committer):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'),
    "git_user_email": re.compile(r'\b<([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})>\b'),
    "api_key_generic": re.compile(r'\b(api_key|apikey|secret|password|token)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?'),
}

# Directories to scan
SCAN_DIRECTORIES = [
    "data/processed",
    "data/generated",
    "results",
    "state",
    "code",  # Scan code for accidental secrets in comments
]

# Extensions to scan
SCANNABLE_EXTENSIONS = {
    '.py', '.txt', '.md', '.csv', '.json', '.yaml', '.yml', '.log', '.html', '.css', '.js'
}

# Files to skip (known safe or binary)
SKIP_FILES = {
    'artifact_hashes.yaml', # Hashes are safe
    '.gitignore',
    'requirements.txt',
    'pyproject.toml',
    'bandit_config.yaml',
    'cwe_patterns.yaml',
}

def is_binary_file(file_path: Path) -> bool:
    """Quick check to skip binary files."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
        return False
    except Exception:
        return True

def scan_file(file_path: Path, patterns: Dict[str, re.Pattern]) -> List[Dict[str, Any]]:
    """Scan a single file for PII patterns."""
    findings = []
    try:
        # Skip binary files
        if is_binary_file(file_path):
            return findings

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for category, pattern in patterns.items():
                matches = pattern.findall(line)
                if matches:
                    # Handle groups in regex (e.g., git_user_name captures just the name)
                    # If match is a tuple (from groups), join or pick relevant part
                    for match in matches:
                        if isinstance(match, tuple):
                            # If it's a tuple, usually the full match is at index 0 or we need to reconstruct
                            # For simplicity, if it's a tuple, we take the non-empty parts
                            match_str = " ".join([m for m in match if m])
                        else:
                            match_str = match
                        
                        # Mask the PII for the log (show only first/last char)
                        masked = match_str[:2] + "..." + match_str[-2:] if len(match_str) > 4 else "***"
                        
                        findings.append({
                            "file": str(file_path),
                            "line": line_num,
                            "category": category,
                            "match": masked, # Don't log real PII
                            "raw_match": match_str, # Keep raw for internal check if needed, but be careful
                            "context": line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                        })
    except Exception as e:
        logger.warning(f"Could not scan {file_path}: {e}")
    
    return findings

def run_security_audit() -> Dict[str, Any]:
    """
    Run the full security audit across the project.
    Returns a summary report.
    """
    logger.info("Starting Security Audit (PII Leakage Detection)...")
    start_time = datetime.now()
    
    all_findings = []
    scanned_files = 0
    skipped_files = 0

    for base_dir in SCAN_DIRECTORIES:
        base_path = Path(base_dir)
        if not base_path.exists():
            logger.warning(f"Directory not found, skipping: {base_dir}")
            continue

        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                # Check extensions
                if file_path.suffix.lower() not in SCANNABLE_EXTENSIONS:
                    skipped_files += 1
                    continue
                
                # Check skip list
                if file_path.name in SKIP_FILES:
                    skipped_files += 1
                    continue

                scanned_files += 1
                findings = scan_file(file_path, PII_PATTERNS)
                if findings:
                    all_findings.extend(findings)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Generate Report
    report = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "summary": {
            "total_files_scanned": scanned_files,
            "files_skipped": skipped_files,
            "total_findings": len(all_findings),
            "severity": "CRITICAL" if any(f["category"] in ["aws_access_key", "github_token", "slack_token", "api_key_generic"] for f in all_findings) else "WARNING" if all_findings else "PASS"
        },
        "findings": all_findings
    }

    return report

def save_report(report: Dict[str, Any], output_path: Path):
    """Save the audit report to a JSON file."""
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # We save the full report, but in a real production scenario, 
    # we might want to strip 'raw_match' before saving to disk to prevent accidental leakage.
    # For this audit, we save the 'masked' version in the main report and keep 'raw_match' 
    # only in memory if we were doing immediate remediation. 
    # Here, we strip raw_match from the saved JSON to be safe.
    safe_findings = []
    for f in report["findings"]:
        safe_f = f.copy()
        safe_f.pop("raw_match", None) # Remove the raw PII from the saved file
        safe_f.pop("context", None) # Remove context which might contain PII
        safe_findings.append(safe_f)
    
    report["findings"] = safe_findings

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Security audit report saved to: {output_path}")

def main():
    """Main entry point."""
    report = run_security_audit()
    
    # Save report to results/security_audit.json
    output_path = Path("results/security_audit.json")
    save_report(report, output_path)

    # Print summary to console
    print("\n" + "="*60)
    print("SECURITY AUDIT SUMMARY")
    print("="*60)
    print(f"Files Scanned: {report['summary']['total_files_scanned']}")
    print(f"Findings:      {report['summary']['total_findings']}")
    print(f"Severity:      {report['summary']['severity']}")
    print(f"Duration:      {report['duration_seconds']:.2f}s")
    print("="*60)

    if report['summary']['findings']:
        print("\n⚠️  PII or Secrets detected. Review 'results/security_audit.json' for details.")
        # Show first 5 findings
        for i, f in enumerate(report['findings'][:5]):
            print(f"  [{i+1}] {f['category']} found in {f['file']} (Line {f['line']})")
        if len(report['findings']) > 5:
            print(f"  ... and {len(report['findings']) - 5} more.")
        return 1 # Exit with error code if findings exist
    else:
        print("\n✅ No PII or secrets detected in scanned artifacts.")
        return 0

if __name__ == "__main__":
    exit(main())
