import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing utilities
from utils.validators import scan_pii, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PII Patterns for hardening (supplementary to validators.py)
PII_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
    'phone_us': re.compile(r'(\+1[-.]?)?(\(?\d{3}\)?[-.]?)?\d{3}[-.]?\d{4}'),
    'ssn': re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'github_token': re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'),
    'api_key': re.compile(r'[Aa][Pp][Ii]_?[Kk][Ee][Yy]\s*[:=]\s*[\'"]?[A-Za-z0-9]{20,}[\'"]?'),
    'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
    'slack_token': re.compile(r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}'),
}

def scan_file_for_pii(file_path: Path, patterns: Optional[Dict[str, re.Pattern]] = None) -> List[Dict[str, Any]]:
    """
    Scan a single file for PII patterns.
    
    Args:
        file_path: Path to the file to scan
        patterns: Dictionary of pattern names to compiled regex objects. 
                 Defaults to PII_PATTERNS if not provided.
    
    Returns:
        List of dictionaries containing match details
    """
    if patterns is None:
        patterns = PII_PATTERNS
    
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in patterns.items():
                matches = pattern.finditer(line)
                for match in matches:
                    findings.append({
                        'file': str(file_path),
                        'line_number': line_num,
                        'pattern_type': pattern_name,
                        'match_text': match.group()[:50] + '...' if len(match.group()) > 50 else match.group(),
                        'start_position': match.start(),
                        'end_position': match.end(),
                        'context': line.strip()[:100]
                    })
    except Exception as e:
        logger.error(f"Error scanning {file_path}: {e}")
        raise
    
    return findings

def scan_directory_for_pii(
    directory: Path, 
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    patterns: Optional[Dict[str, re.Pattern]] = None
) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for PII patterns.
    
    Args:
        directory: Root directory to scan
        extensions: List of file extensions to include (e.g., ['.py', '.json', '.txt'])
                   If None, scans all files
        exclude_dirs: List of directory names to exclude from scanning
        patterns: Custom patterns to use
    
    Returns:
        List of all PII findings across the directory
    """
    if extensions is None:
        extensions = ['.py', '.json', '.yaml', '.yml', '.txt', '.md', '.csv', '.parquet']
    
    if exclude_dirs is None:
        exclude_dirs = ['__pycache__', '.git', 'node_modules', '.venv', 'env', 'venv']
    
    all_findings = []
    excluded_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = Path(root) / file
            
            # Check extension
            if extensions and file_path.suffix not in extensions:
                continue
            
            try:
                findings = scan_file_for_pii(file_path, patterns)
                all_findings.extend(findings)
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")
    
    logger.info(f"Scanned directory: {directory}")
    logger.info(f"Found {len(all_findings)} potential PII instances")
    
    return all_findings

def generate_pii_report(
    findings: List[Dict[str, Any]],
    output_path: Path,
    severity_threshold: str = 'medium'
) -> Dict[str, Any]:
    """
    Generate a comprehensive PII scan report.
    
    Args:
        findings: List of PII findings from scan functions
        output_path: Path to write the JSON report
        severity_threshold: Minimum severity to include ('low', 'medium', 'high', 'critical')
    
    Returns:
        Report dictionary containing summary and findings
    """
    # Define severity levels
    severity_map = {
        'email': 'medium',
        'phone_us': 'medium',
        'ssn': 'critical',
        'credit_card': 'critical',
        'ip_address': 'low',
        'github_token': 'critical',
        'api_key': 'critical',
        'aws_access_key': 'critical',
        'slack_token': 'critical'
    }
    
    severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    threshold_level = severity_order.get(severity_threshold, 2)
    
    # Filter findings by severity
    filtered_findings = []
    for finding in findings:
        pattern_type = finding.get('pattern_type', 'unknown')
        severity = severity_map.get(pattern_type, 'low')
        if severity_order.get(severity, 1) >= threshold_level:
            finding['severity'] = severity
            filtered_findings.append(finding)
    
    # Generate summary
    summary = {
        'scan_timestamp': datetime.now().isoformat(),
        'total_findings': len(filtered_findings),
        'severity_breakdown': {},
        'pattern_breakdown': {},
        'files_affected': set()
    }
    
    for finding in filtered_findings:
        severity = finding.get('severity', 'unknown')
        pattern_type = finding.get('pattern_type', 'unknown')
        file_path = finding.get('file', 'unknown')
        
        summary['severity_breakdown'][severity] = summary['severity_breakdown'].get(severity, 0) + 1
        summary['pattern_breakdown'][pattern_type] = summary['pattern_breakdown'].get(pattern_type, 0) + 1
        summary['files_affected'].add(file_path)
    
    summary['files_affected'] = list(summary['files_affected'])
    summary['files_affected_count'] = len(summary['files_affected'])
    
    # Create report
    report = {
        'summary': summary,
        'findings': filtered_findings
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"PII report written to {output_path}")
    return report

def enforce_pii_policy(
    findings: List[Dict[str, Any]],
    block_on_critical: bool = True,
    block_on_high: bool = False
) -> Tuple[bool, str]:
    """
    Enforce PII policy based on findings.
    
    Args:
        findings: List of PII findings
        block_on_critical: If True, return False if any critical findings exist
        block_on_high: If True, return False if any high/critical findings exist
    
    Returns:
        Tuple of (is_compliant, message)
    """
    critical_count = 0
    high_count = 0
    
    severity_map = {
        'email': 'medium',
        'phone_us': 'medium',
        'ssn': 'critical',
        'credit_card': 'critical',
        'ip_address': 'low',
        'github_token': 'critical',
        'api_key': 'critical',
        'aws_access_key': 'critical',
        'slack_token': 'critical'
    }
    
    for finding in findings:
        pattern_type = finding.get('pattern_type', 'unknown')
        severity = severity_map.get(pattern_type, 'low')
        
        if severity == 'critical':
            critical_count += 1
        elif severity == 'high':
            high_count += 1
    
    if block_on_critical and critical_count > 0:
        return False, f"Policy violation: {critical_count} critical PII instances found"
    
    if block_on_high and (high_count + critical_count) > 0:
        return False, f"Policy violation: {high_count + critical_count} high/critical PII instances found"
    
    return True, "PII policy check passed"

def run_pii_scan_pipeline(
    scan_paths: List[Path],
    output_dir: Path,
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    severity_threshold: str = 'medium',
    block_on_critical: bool = True
) -> Dict[str, Any]:
    """
    Run a complete PII scan pipeline on multiple paths.
    
    Args:
        scan_paths: List of files or directories to scan
        output_dir: Directory to write reports
        extensions: File extensions to include
        exclude_dirs: Directories to exclude
        severity_threshold: Minimum severity level to report
        block_on_critical: Whether to fail on critical findings
    
    Returns:
        Pipeline execution results
    """
    start_time = datetime.now()
    all_findings = []
    
    logger.info(f"Starting PII scan pipeline on {len(scan_paths)} paths")
    
    for path in scan_paths:
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            continue
        
        if path.is_dir():
            logger.info(f"Scanning directory: {path}")
            findings = scan_directory_for_pii(path, extensions, exclude_dirs)
        elif path.is_file():
            logger.info(f"Scanning file: {path}")
            findings = scan_file_for_pii(path)
        else:
            logger.warning(f"Unknown path type: {path}")
            continue
        
        all_findings.extend(findings)
    
    # Generate report
    report_path = output_dir / 'pii_scan_report.json'
    report = generate_pii_report(all_findings, report_path, severity_threshold)
    
    # Enforce policy
    is_compliant, message = enforce_pii_policy(all_findings, block_on_critical)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    result = {
        'status': 'passed' if is_compliant else 'failed',
        'message': message,
        'scan_duration_seconds': duration,
        'report_path': str(report_path),
        'summary': report['summary']
    }
    
    logger.info(f"PII scan pipeline completed: {result['status']}")
    return result

def main():
    """Main entry point for PII scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan codebase for PII and enforce security policies')
    parser.add_argument('--paths', nargs='+', required=True, help='Paths to scan (files or directories)')
    parser.add_argument('--output-dir', default='data/processed', help='Output directory for reports')
    parser.add_argument('--extensions', nargs='+', default=None, help='File extensions to include')
    parser.add_argument('--exclude-dirs', nargs='+', default=None, help='Directories to exclude')
    parser.add_argument('--severity-threshold', default='medium', choices=['low', 'medium', 'high', 'critical'])
    parser.add_argument('--no-block-critical', action='store_true', help='Do not block on critical findings')
    
    args = parser.parse_args()
    
    scan_paths = [Path(p) for p in args.paths]
    output_dir = Path(args.output_dir)
    
    result = run_pii_scan_pipeline(
        scan_paths=scan_paths,
        output_dir=output_dir,
        extensions=args.extensions,
        exclude_dirs=args.exclude_dirs,
        severity_threshold=args.severity_threshold,
        block_on_critical=not args.no_block_critical
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print("PII SCAN RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    print(f"Duration: {result['scan_duration_seconds']:.2f} seconds")
    print(f"Report: {result['report_path']}")
    print(f"Total Findings: {result['summary']['total_findings']}")
    print(f"Files Affected: {result['summary']['files_affected_count']}")
    
    if result['summary']['severity_breakdown']:
        print("\nSeverity Breakdown:")
        for severity, count in result['summary']['severity_breakdown'].items():
            print(f"  {severity.upper()}: {count}")
    
    if result['status'] == 'failed':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
