"""
PII Scanner Module for the llmXive pipeline.

Implements regex-based detection of Personally Identifiable Information (PII)
including Email addresses, US Phone numbers, and US Social Security Numbers (SSN).

Public API:
- PIIScanResult: TypedDict for scan results
- scan_text: Scan a string for PII patterns
- scan_dataframe: Scan all string columns in a DataFrame
- generate_report: Write scan findings to a JSON file
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define regex patterns for PII detection
# Email: Standard RFC 5322 simplified pattern
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Phone: US formats (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, XXXXXXXXXX
PHONE_PATTERN = re.compile(
    r'(?:\+1[-.\s]?)?'
    r'(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}',
    re.IGNORECASE
)

# SSN: XXX-XX-XXXX (strict format with dashes)
SSN_PATTERN = re.compile(
    r'\b\d{3}-\d{2}-\d{4}\b'
)

class PIIScanResult:
    """Data structure for PII scan results."""
    
    def __init__(
        self,
        text_id: Optional[str] = None,
        email_count: int = 0,
        phone_count: int = 0,
        ssn_count: int = 0,
        findings: Dict[str, List[str]] = None
    ):
        self.text_id = text_id
        self.email_count = email_count
        self.phone_count = phone_count
        self.ssn_count = ssn_count
        self.findings = findings or {
            'emails': [],
            'phones': [],
            'ssns': []
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'text_id': self.text_id,
            'email_count': self.email_count,
            'phone_count': self.phone_count,
            'ssn_count': self.ssn_count,
            'total_findings': self.email_count + self.phone_count + self.ssn_count,
            'findings': self.findings
        }

def scan_text(text: str, text_id: Optional[str] = None) -> PIIScanResult:
    """
    Scan a string for PII patterns (email, phone, SSN).
    
    Args:
        text: The input string to scan.
        text_id: Optional identifier for the text source.
        
    Returns:
        PIIScanResult containing counts and lists of found PII.
    """
    result = PIIScanResult(text_id=text_id)
    
    # Find emails
    emails = EMAIL_PATTERN.findall(text)
    result.email_count = len(emails)
    result.findings['emails'] = list(set(emails))  # Deduplicate
    
    # Find phones
    phones = PHONE_PATTERN.findall(text)
    result.phone_count = len(phones)
    result.findings['phones'] = list(set(phones))
    
    # Find SSNs
    ssns = SSN_PATTERN.findall(text)
    result.ssn_count = len(ssns)
    result.findings['ssns'] = list(set(ssns))
    
    return result

def scan_dataframe(df: Any, columns: Optional[List[str]] = None) -> List[PIIScanResult]:
    """
    Scan string columns in a pandas DataFrame for PII.
    
    Args:
        df: Pandas DataFrame to scan.
        columns: Optional list of column names to scan. If None, scans all string columns.
        
    Returns:
        List of PIIScanResult objects, one per row.
    """
    import pandas as pd
    
    results = []
    
    # Determine columns to scan
    if columns is None:
        # Select only object/string columns
        columns = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    for idx, row in df.iterrows():
        row_text = " ".join(
            str(row[col]) if pd.notna(row[col]) else ""
            for col in columns
        )
        
        result = scan_text(row_text, text_id=str(idx))
        results.append(result)
    
    return results

def generate_report(
    results: List[PIIScanResult],
    output_path: str | Path,
    overwrite: bool = False
) -> Path:
    """
    Generate a JSON report of PII scan findings.
    
    Args:
        results: List of PIIScanResult objects.
        output_path: Path to write the JSON report.
        overwrite: If False, raises FileExistsError if file exists.
        
    Returns:
        Path to the generated report.
    """
    output_path = Path(output_path)
    
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Report file already exists: {output_path}")
    
    # Aggregate statistics
    total_emails = sum(r.email_count for r in results)
    total_phones = sum(r.phone_count for r in results)
    total_ssns = sum(r.ssn_count for r in results)
    total_findings = total_emails + total_phones + total_ssns
    
    report = {
        'summary': {
            'total_items_scanned': len(results),
            'items_with_findings': sum(1 for r in results if r.total_findings > 0),
            'total_findings': total_findings,
            'breakdown': {
                'emails': total_emails,
                'phones': total_phones,
                'ssns': total_ssns
            }
        },
        'detailed_results': [r.to_dict() for r in results]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return output_path