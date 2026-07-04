"""
PII Scanner Module for the llmXive pipeline.

Provides functionality to scan text data for Personally Identifiable Information (PII)
including Email addresses, US Phone numbers, and Social Security Numbers (SSN).
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


# Compile regex patterns for efficiency
PATTERNS = {
    "email": re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    ),
    "phone": re.compile(
        r"(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?"
    ),
    "ssn": re.compile(
        r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
    )
}


class PIIScanResult:
    """Container for PII scan results."""

    def __init__(self, text: str, findings: Dict[str, List[str]]):
        self.text = text
        self.findings = findings
        self.is_clean = len(findings) == 0
        self.total_findings = sum(len(v) for v in findings.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_preview": self.text[:100] + ("..." if len(self.text) > 100 else ""),
            "is_clean": self.is_clean,
            "total_findings": self.total_findings,
            "findings": self.findings
        }


def scan_text(text: str, pattern_types: Optional[List[str]] = None) -> PIIScanResult:
    """
    Scan a single string for PII patterns.

    Args:
        text: The string to scan.
        pattern_types: Optional list of pattern keys to scan for ('email', 'phone', 'ssn').
                       If None, scans for all defined patterns.

    Returns:
        PIIScanResult object containing matches.
    """
    if pattern_types is None:
        pattern_types = list(PATTERNS.keys())

    findings: Dict[str, List[str]] = {}

    for p_type in pattern_types:
        if p_type not in PATTERNS:
            raise ValueError(f"Unknown pattern type: {p_type}. Valid types: {list(PATTERNS.keys())}")
        
        matches = PATTERNS[p_type].findall(text)
        if matches:
            # Handle regex groups: findall returns tuples if groups exist
            # Flatten tuples to strings if necessary
            clean_matches = []
            for match in matches:
                if isinstance(match, tuple):
                    # For phone numbers, we often get tuples of groups. 
                    # Join non-empty parts or take the full match if we used groups loosely.
                    # Here we rely on the fact that findall might return groups.
                    # To be safe and get the actual substring, we should use finditer or handle groups.
                    # However, for simple extraction, let's re-run finditer for precision if groups exist.
                    # But for this implementation, let's assume the regex captures the whole entity or we handle the tuple.
                    # The phone regex above has groups. Let's refine the approach to get the full match string.
                    pass 
            
            # Re-implement using finditer to get the actual matched string (match.group(0))
            # This avoids issues with capturing groups in the regex definition
            current_matches = []
            for m in PATTERNS[p_type].finditer(text):
                current_matches.append(m.group(0))
            
            if current_matches:
                findings[p_type] = current_matches

    return PIIScanResult(text, findings)


def scan_dataframe(df, text_column: str, pattern_types: Optional[List[str]] = None) -> List[PIIScanResult]:
    """
    Scan a pandas DataFrame column for PII.

    Args:
        df: The pandas DataFrame.
        text_column: Name of the column containing text to scan.
        pattern_types: Optional list of pattern types to check.

    Returns:
        List of PIIScanResult objects, one per row.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for scan_dataframe. Install via pip install pandas")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in DataFrame")

    results = []
    for idx, row in df.iterrows():
        val = row[text_column]
        if pd.isna(val) or not isinstance(val, str):
            # Treat non-strings as empty/no PII
            results.append(PIIScanResult(str(val) if val is not None else "", {}))
        else:
            results.append(scan_text(val, pattern_types))
    
    return results


def generate_report(results: List[PIIScanResult], output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a summary report of PII scan results.

    Args:
        results: List of PIIScanResult objects.
        output_path: Optional path to save the report as JSON.

    Returns:
        Dictionary containing the summary report.
    """
    total_scanned = len(results)
    clean_count = sum(1 for r in results if r.is_clean)
    flagged_count = total_scanned - clean_count

    summary = {
        "total_records": total_scanned,
        "clean_records": clean_count,
        "flagged_records": flagged_count,
        "clean_percentage": (clean_count / total_scanned * 100) if total_scanned > 0 else 0.0,
        "findings_by_type": {
            "email": 0,
            "phone": 0,
            "ssn": 0
        },
        "details": [r.to_dict() for r in results if not r.is_clean]
    }

    # Aggregate counts
    for r in results:
        for p_type, matches in r.findings.items():
            if p_type in summary["findings_by_type"]:
                summary["findings_by_type"][p_type] += len(matches)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    # Simple CLI for testing the scanner directly
    sample_text = """
    Contact us at support@example.com or call 1-800-555-0199.
    My SSN is 123-45-6789.
    Another email: user.name+tag@domain.co.uk.
    Phone: (555) 123-4567.
    No PII here.
    """
    
    print("Running PII Scanner on sample text...")
    result = scan_text(sample_text)
    print(json.dumps(result.to_dict(), indent=2))