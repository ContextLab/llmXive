"""
Reference Validator for Citation Verification.

Implements Constitution Principle II: All scientific claims must be backed by
verifiable citations. This module validates that references in the research
pipeline point to real, accessible sources.
"""
import logging
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass, asdict
from datetime import datetime

import requests

from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration for validation
DOI_REGEX = re.compile(
    r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', 
    re.IGNORECASE
)
ARXIV_REGEX = re.compile(
    r'arXiv:\d{4}\.\d{4,5}(v\d+)?',
    re.IGNORECASE
)
PUBMED_REGEX = re.compile(
    r'PMID:\s*\d+',
    re.IGNORECASE
)

# Timeouts for network requests (seconds)
DOI_TIMEOUT = 10
ARXIV_TIMEOUT = 15
PUBMED_TIMEOUT = 10

@dataclass
class ValidationResult:
    """Result of a single reference validation."""
    reference_id: str
    reference_text: str
    is_valid: bool
    source_type: str  # 'doi', 'arxiv', 'pubmed', 'unknown', 'url'
    resolved_url: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    validated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ValidationReport:
    """Aggregated validation report."""
    total_references: int
    valid_count: int
    invalid_count: int
    unknown_count: int
    results: List[Dict[str, Any]]
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def extract_references(text: str) -> List[Dict[str, str]]:
    """
    Extract potential references from text content.
    
    Looks for DOIs, arXiv IDs, PubMed IDs, and URLs.
    
    Args:
        text: The text content to scan for references.
        
    Returns:
        List of dicts with 'id', 'text', and 'type' keys.
    """
    references = []
    
    # Extract DOIs
    for match in DOI_REGEX.finditer(text):
        references.append({
            'id': match.group(0),
            'text': match.group(0),
            'type': 'doi'
        })
    
    # Extract arXiv IDs
    for match in ARXIV_REGEX.finditer(text):
        references.append({
            'id': match.group(0),
            'text': match.group(0),
            'type': 'arxiv'
        })
    
    # Extract PubMed IDs
    for match in PUBMED_REGEX.finditer(text):
        references.append({
            'id': match.group(0).replace('PMID:', '').strip(),
            'text': match.group(0),
            'type': 'pubmed'
        })
    
    # Extract URLs (basic pattern)
    url_pattern = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        re.IGNORECASE
    )
    for match in url_pattern.finditer(text):
        url = match.group(0).rstrip('.')
        # Skip if it's part of a DOI resolution URL
        if not url.startswith('https://doi.org/') and not url.startswith('http://doi.org/'):
            references.append({
                'id': url,
                'text': url,
                'type': 'url'
            })
    
    return references

def validate_doi(doi: str, timeout: int = DOI_TIMEOUT) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate a DOI by checking if it resolves.
    
    Args:
        doi: The DOI string to validate.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_valid, resolved_url, status_code)
    """
    url = f"https://doi.org/{doi}"
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, response.url, response.status_code
        elif response.status_code == 404:
            return False, None, response.status_code
        else:
            # Try GET as fallback for HEAD failures
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return True, response.url, response.status_code
            return False, None, response.status_code
    except requests.exceptions.RequestException as e:
        logger.warning(f"DOI validation failed for {doi}: {e}")
        return False, None, None

def validate_arxiv(arxiv_id: str, timeout: int = ARXIV_TIMEOUT) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate an arXiv ID.
    
    Args:
        arxiv_id: The arXiv ID string (e.g., 'arXiv:2101.12345').
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_valid, resolved_url, status_code)
    """
    # Normalize ID
    clean_id = arxiv_id.replace('arXiv:', '').strip()
    url = f"https://arxiv.org/abs/{clean_id}"
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, response.url, response.status_code
        else:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, response.url, response.status_code
            return False, None, response.status_code
    except requests.exceptions.RequestException as e:
        logger.warning(f"arXiv validation failed for {arxiv_id}: {e}")
        return False, None, None

def validate_pubmed(pmid: str, timeout: int = PUBMED_TIMEOUT) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate a PubMed ID.
    
    Args:
        pmid: The PubMed ID string.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_valid, resolved_url, status_code)
    """
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, response.url, response.status_code
        else:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, response.url, response.status_code
            return False, None, response.status_code
    except requests.exceptions.RequestException as e:
        logger.warning(f"PubMed validation failed for {pmid}: {e}")
        return False, None, None

def validate_url(url: str, timeout: int = 10) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate a generic URL.
    
    Args:
        url: The URL to validate.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_valid, resolved_url, status_code)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, response.url, response.status_code
        else:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, response.url, response.status_code
            return False, None, response.status_code
    except requests.exceptions.RequestException as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        return False, None, None

def validate_reference(ref: Dict[str, str]) -> ValidationResult:
    """
    Validate a single reference based on its type.
    
    Args:
        ref: Dict with 'id', 'text', and 'type' keys.
        
    Returns:
        ValidationResult object.
    """
    ref_type = ref['type']
    ref_id = ref['id']
    ref_text = ref['text']
    
    is_valid = False
    resolved_url = None
    status_code = None
    error_message = None
    
    if ref_type == 'doi':
        is_valid, resolved_url, status_code = validate_doi(ref_id)
    elif ref_type == 'arxiv':
        is_valid, resolved_url, status_code = validate_arxiv(ref_id)
    elif ref_type == 'pubmed':
        is_valid, resolved_url, status_code = validate_pubmed(ref_id)
    elif ref_type == 'url':
        is_valid, resolved_url, status_code = validate_url(ref_id)
    else:
        error_message = f"Unknown reference type: {ref_type}"
    
    return ValidationResult(
        reference_id=ref_id,
        reference_text=ref_text,
        is_valid=is_valid,
        source_type=ref_type,
        resolved_url=resolved_url,
        status_code=status_code,
        error_message=error_message,
        validated_at=datetime.utcnow().isoformat()
    )

def validate_references_in_file(
    file_path: Path,
    output_path: Optional[Path] = None
) -> ValidationReport:
    """
    Scan a file for references and validate them.
    
    Args:
        file_path: Path to the file to scan.
        output_path: Optional path to write the JSON report.
        
    Returns:
        ValidationReport object.
    """
    logger.info(f"Scanning file for references: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    references = extract_references(content)
    logger.info(f"Found {len(references)} potential references in {file_path}")
    
    results = []
    valid_count = 0
    invalid_count = 0
    unknown_count = 0
    
    for ref in references:
        result = validate_reference(ref)
        results.append(result.to_dict())
        
        if result.is_valid:
            valid_count += 1
        elif result.error_message and "Unknown reference type" in result.error_message:
            unknown_count += 1
        else:
            invalid_count += 1
    
    report = ValidationReport(
        total_references=len(references),
        valid_count=valid_count,
        invalid_count=invalid_count,
        unknown_count=unknown_count,
        results=results,
        generated_at=datetime.utcnow().isoformat()
    )
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Validation report written to {output_path}")
    
    return report

def validate_citation_list(
    citations: List[str],
    output_path: Optional[Path] = None
) -> ValidationReport:
    """
    Validate a list of citation strings.
    
    Args:
        citations: List of citation strings to validate.
        output_path: Optional path to write the JSON report.
        
    Returns:
        ValidationReport object.
    """
    logger.info(f"Validating {len(citations)} citation strings")
    
    # Parse each citation string into references
    all_refs = []
    for i, citation_text in enumerate(citations):
        refs = extract_references(citation_text)
        for ref in refs:
            ref['source_index'] = i
        all_refs.extend(refs)
    
    results = []
    valid_count = 0
    invalid_count = 0
    unknown_count = 0
    
    for ref in all_refs:
        result = validate_reference(ref)
        results.append(result.to_dict())
        
        if result.is_valid:
            valid_count += 1
        elif result.error_message and "Unknown reference type" in result.error_message:
            unknown_count += 1
        else:
            invalid_count += 1
    
    report = ValidationReport(
        total_references=len(all_refs),
        valid_count=valid_count,
        invalid_count=invalid_count,
        unknown_count=unknown_count,
        results=results,
        generated_at=datetime.utcnow().isoformat()
    )
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Validation report written to {output_path}")
    
    return report

def verify_documentation_references(
    docs_dir: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, ValidationReport]:
    """
    Scan all markdown and text files in a documentation directory for references.
    
    Args:
        docs_dir: Path to the documentation directory.
        output_dir: Optional directory to write individual reports.
        
    Returns:
        Dict mapping file paths to their ValidationReport objects.
    """
    if not docs_dir.exists():
        raise FileNotFoundError(f"Directory not found: {docs_dir}")
    
    reports = {}
    files = list(docs_dir.glob("**/*.md")) + list(docs_dir.glob("**/*.txt"))
    
    logger.info(f"Scanning {len(files)} documentation files")
    
    for file_path in files:
        try:
            output_file = None
            if output_dir:
                relative_path = file_path.relative_to(docs_dir)
                output_file = output_dir / f"{relative_path.stem}_validation.json"
            
            report = validate_references_in_file(file_path, output_file)
            reports[str(file_path)] = report
            
            logger.info(
                f"Validated {file_path}: "
                f"{report.valid_count} valid, "
                f"{report.invalid_count} invalid, "
                f"{report.unknown_count} unknown"
            )
        except Exception as e:
            logger.error(f"Failed to validate {file_path}: {e}")
    
    return reports

def generate_summary_report(
    reports: Dict[str, ValidationReport],
    output_path: Path
) -> None:
    """
    Generate a summary report from multiple validation reports.
    
    Args:
        reports: Dict mapping file paths to ValidationReport objects.
        output_path: Path to write the summary JSON.
    """
    total_refs = sum(r.total_references for r in reports.values())
    total_valid = sum(r.valid_count for r in reports.values())
    total_invalid = sum(r.invalid_count for r in reports.values())
    total_unknown = sum(r.unknown_count for r in reports.values())
    
    summary = {
        "summary": {
            "total_files": len(reports),
            "total_references": total_refs,
            "valid_count": total_valid,
            "invalid_count": total_invalid,
            "unknown_count": total_unknown,
            "success_rate": total_valid / total_refs if total_refs > 0 else 0.0
        },
        "file_breakdown": {
            path: report.to_dict() 
            for path, report in reports.items()
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary report written to {output_path}")