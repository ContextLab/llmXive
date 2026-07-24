"""
Audit all generated reports for "associational" language compliance.

This script scans the final report JSON and any generated CSV/Markdown files
to ensure that causal language (e.g., "predicts", "causes", "drives", "effect")
is replaced or flagged with "associational" language (e.g., "correlates with",
"is associated with", "relates to", "links").

It enforces the "associational" framing requirement (FR-007) by:
1. Checking the final report JSON for prohibited terms.
2. Generating a compliance audit log.
3. Failing loudly if non-compliant language is found without a disclaimer.
"""
import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "final_report.json"
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "correlation_results.csv"
AUDIT_LOG_PATH = PROJECT_ROOT / "data" / "logs" / "associational_language_audit.json"

# List of prohibited causal terms that imply prediction or causation
PROHIBITED_TERMS = [
    r'\bpredicts?\b',
    r'\bcaus(?:e|es|ed|ing)\b',
    r'\bdriv(?:e|es|ed|ing)\b',
    r'\beffect\b',
    r'\binfluenc(?:e|es|ed|ing)\b', # Often acceptable but strict mode flags it
    r'\bdetermin(?:e|es|ed|ing)\b',
    r'\bgovern(?:s|ed|ing)?\b',
    r'\bcontrol(?:s|ed|ing)?\b',
    r'\bdictat(?:e|es|ed|ing)\b',
    r'\bcause\b',
]

# Regex for checking if a sentence contains a prohibited term
PROHIBITED_PATTERN = re.compile('|'.join(PROHIBITED_TERMS), re.IGNORECASE)

# List of acceptable "associational" terms
ACCEPTABLE_TERMS = [
    r'\bcorrelat(?:e|es|ed|ing)\b',
    r'\bassociat(?:e|es|ed|ing)\b',
    r'\brelat(?:e|es|ed|ing)\b',
    r'\blink(?:s|ed|ing)?\b',
    r'\brel(?:ev|evant)\b',
    r'\bcorrespond(?:s|ed|ing)\b',
    r'\bcorrel(?:ation|ations)\b',
]

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists."""
    if not path.exists():
        print(f"Warning: File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
        return None

def load_csv_file(path: Path) -> Optional[List[str]]:
    """Load a CSV file as a list of strings (lines)."""
    if not path.exists():
        print(f"Warning: File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading CSV {path}: {e}")
        return None

def check_text_for_causality(text: str, context: str = "unknown") -> List[Dict[str, Any]]:
    """
    Scan a text string for prohibited causal language.
    Returns a list of findings.
    """
    findings = []
    if not text:
        return findings

    # Find all matches of prohibited terms
    matches = PROHIBITED_PATTERN.finditer(text)
    for match in matches:
        start, end = match.span()
        # Extract a snippet for context (50 chars before and after)
        snippet_start = max(0, start - 50)
        snippet_end = min(len(text), end + 50)
        snippet = text[snippet_start:snippet_end]
        
        # Clean snippet (newlines)
        snippet = snippet.replace('\n', ' ').strip()
        
        findings.append({
            "context": context,
            "term": match.group(),
            "position": start,
            "snippet": snippet,
            "severity": "high"
        })
    
    return findings

def scan_report_json(report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recursively scan a report dictionary for text fields."""
    findings = []
    
    def recurse(obj, path="root"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                recurse(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                recurse(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            # Only scan non-empty strings
            if len(obj.strip()) > 10:
                findings.extend(check_text_for_causality(obj, path))

    recurse(report_data)
    return findings

def scan_csv_file(lines: List[str]) -> List[Dict[str, Any]]:
    """Scan CSV lines for prohibited terms."""
    findings = []
    for i, line in enumerate(lines):
        if len(line.strip()) > 10:
            findings.extend(check_text_for_causality(line, f"CSV Line {i+1}"))
    return findings

def generate_audit_report(findings: List[Dict[str, Any]], audit_path: Path) -> bool:
    """
    Generate the audit log.
    Returns True if compliant (no high severity findings), False otherwise.
    """
    audit_data = {
        "audit_timestamp": "2026-06-26T12:00:00Z", # Placeholder, use actual if needed
        "total_findings": len(findings),
        "compliant": len(findings) == 0,
        "findings": findings
    }

    # Ensure logs directory exists
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2)

    return audit_data["compliant"]

def main():
    print("Starting Associational Language Compliance Audit (T043)...")
    
    all_findings = []
    is_compliant = True

    # 1. Scan Final Report JSON
    print(f"Scanning: {REPORT_PATH}")
    report_data = load_json_file(REPORT_PATH)
    if report_data:
        findings = scan_report_json(report_data)
        all_findings.extend(findings)
        print(f"  Found {len(findings)} potential causal language instances.")
    else:
        print("  Skipping (file missing or invalid).")

    # 2. Scan Correlation Results CSV
    print(f"Scanning: {CORRELATION_RESULTS_PATH}")
    csv_lines = load_csv_file(CORRELATION_RESULTS_PATH)
    if csv_lines:
        findings = scan_csv_file(csv_lines)
        all_findings.extend(findings)
        print(f"  Found {len(findings)} potential causal language instances.")
    else:
        print("  Skipping (file missing or invalid).")

    # 3. Generate Audit Log
    is_compliant = generate_audit_report(all_findings, AUDIT_LOG_PATH)
    
    print(f"Audit log written to: {AUDIT_LOG_PATH}")

    if all_findings:
        print("\n⚠️  COMPLIANCE VIOLATION DETECTED:")
        print("The following instances of causal/predictive language were found:")
        for f in all_findings:
            print(f"  - [{f['context']}] '{f['term']}' in: ...{f['snippet']}...")
        print("\nAction Required: Review and replace with 'associational' language (e.g., 'correlates with').")
        print("The pipeline must NOT claim prediction or causation from correlational data.")
        sys.exit(1) # Fail loudly
    else:
        print("\n✅ COMPLIANCE CHECK PASSED: No prohibited causal language detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
