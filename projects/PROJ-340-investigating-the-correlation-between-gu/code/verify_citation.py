"""
Citation Verification Module for Real-Data Pipeline.

This module implements T085: Real-Data Citation Verification.
It scans input data files for DOI/citation metadata and validates
them against a local list of verified DOIs.

Addresses Constitution Principle II.
"""
import os
import sys
import json
import yaml
import re
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

class CitationVerificationError(Exception):
    """Raised when citation verification fails."""
    pass

def load_verified_dois(verified_dois_path: str) -> List[str]:
    """
    Load the list of verified DOIs from the YAML configuration file.
    
    Args:
        verified_dois_path: Path to verified_dois.yaml
        
    Returns:
        List of verified DOI strings.
        
    Raises:
        FileNotFoundError: If the verified_dois.yaml file is missing.
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = Path(verified_dois_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Verified DOIs configuration not found at {verified_dois_path}. "
            "Cannot proceed with citation verification."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or 'verified_dois' not in data:
        raise ValueError(
            f"Invalid format in {verified_dois_path}. Expected 'verified_dois' key."
        )
    
    return [str(doi).strip() for doi in data['verified_dois']]

def extract_citation_from_file(data_path: str) -> Optional[str]:
    """
    Extract DOI or citation ID from a CSV data file.
    
    Searches for common metadata columns: 'doi', 'citation', 'source_doi', 'dataset_id'.
    Also checks for a '_metadata' JSON string column if present.
    
    Args:
        data_path: Path to the input CSV file.
        
    Returns:
        The extracted DOI string if found, None otherwise.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    
    # Simple CSV parsing to look for metadata columns
    # We only read the header and first few rows to find metadata
    try:
        with open(path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            headers = [h.strip().lower() for h in header_line.split(',')]
            
            # Look for DOI-related columns
            doi_keywords = ['doi', 'citation', 'source_doi', 'dataset_id', 'source']
            doi_col_idx = None
            
            for i, h in enumerate(headers):
                if any(kw in h for kw in doi_keywords):
                    doi_col_idx = i
                    break
            
            if doi_col_idx is None:
                # Check for a metadata JSON column
                if 'metadata' in headers:
                    meta_idx = headers.index('metadata')
                    # Read first data row
                    first_data = f.readline().strip()
                    if first_data:
                        parts = first_data.split(',')
                        if meta_idx < len(parts):
                            try:
                                meta = json.loads(parts[meta_idx])
                                if 'doi' in meta:
                                    return meta['doi']
                            except json.JSONDecodeError:
                                pass
                return None
            
            # Read the value from the first data row
            first_data = f.readline().strip()
            if first_data:
                parts = first_data.split(',')
                if doi_col_idx < len(parts):
                    value = parts[doi_col_idx].strip()
                    if value and value != 'nan':
                        return value
                    
    except Exception as e:
        # If parsing fails, return None (will be caught by validation)
        print(f"Warning: Could not parse CSV header for citation extraction: {e}")
        return None
    
    return None

def extract_citation_from_url(url: str) -> Optional[str]:
    """
    Attempt to extract a DOI from a URL string.
    
    Common patterns:
    - https://doi.org/10.xxxx/xxxxx
    - https://zenodo.org/record/xxxxx (extracts record ID)
    
    Args:
        url: The URL string to parse.
        
    Returns:
        Extracted DOI or ID, or None if not found.
    """
    if not url:
        return None
    
    # Pattern for DOI URLs
    doi_pattern = r'doi\.org/(10\.\d+/\S+)'
    match = re.search(doi_pattern, url, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern for Zenodo
    zenodo_pattern = r'zenodo\.org/(?:record|records)/(\d+)'
    match = re.search(zenodo_pattern, url, re.IGNORECASE)
    if match:
        return f"10.5281/zenodo.{match.group(1)}"
    
    return None

def verify_citation(extracted_citation: Optional[str], verified_dois: List[str]) -> bool:
    """
    Verify if the extracted citation matches any in the verified list.
    
    Args:
        extracted_citation: The DOI or citation ID found in the data.
        verified_dois: List of approved DOIs.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        CitationVerificationError: If citation is missing or invalid.
    """
    if not extracted_citation:
        raise CitationVerificationError(
            "Citation Verification Failed: No DOI or citation ID found in the input data. "
            "Please ensure the dataset contains a 'doi' or 'citation' column with a valid identifier."
        )
    
    # Normalize the extracted citation (remove leading 'doi:' if present)
    normalized = extracted_citation.strip()
    if normalized.lower().startswith('doi:'):
        normalized = normalized[4:].strip()
    
    # Check against verified list
    is_valid = False
    for v_doi in verified_dois:
        v_normalized = v_doi.strip()
        if v_normalized.lower().startswith('doi:'):
            v_normalized = v_normalized[4:].strip()
        
        if normalized == v_normalized:
            is_valid = True
            break
    
    if not is_valid:
        raise CitationVerificationError(
            f"Citation Verification Failed: The dataset cites '{extracted_citation}', "
            f"which is not in the list of verified DOIs. "
            f"Verified DOIs: {verified_dois}. "
            "Please provide a dataset with a verified citation or add the DOI to data/citations/verified_dois.yaml."
        )
    
    return True

def run_citation_verification(
    data_path: str,
    verified_dois_path: str = "data/citations/verified_dois.yaml"
) -> Dict[str, Any]:
    """
    Main entry point for citation verification.
    
    Args:
        data_path: Path to the input CSV data file.
        verified_dois_path: Path to the verified DOIs configuration.
        
    Returns:
        Dictionary with verification status and details.
        
    Raises:
        CitationVerificationError: If verification fails.
    """
    # Load verified DOIs
    verified_dois = load_verified_dois(verified_dois_path)
    
    # Extract citation from data
    extracted = extract_citation_from_file(data_path)
    
    # If not found in CSV, try URL if present in a config file (optional)
    if not extracted:
        # Check for a .meta file next to the data
        meta_path = Path(data_path).with_suffix('.meta')
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                if 'source_url' in meta:
                    extracted = extract_citation_from_url(meta['source_url'])
                elif 'doi' in meta:
                    extracted = meta['doi']
    
    # Verify
    is_valid = verify_citation(extracted, verified_dois)
    
    return {
        "status": "VERIFIED",
        "citation": extracted,
        "verified": is_valid,
        "message": "Citation successfully verified against the allowed list."
    }

def main():
    """CLI entry point for T085."""
    parser = argparse.ArgumentParser(
        description="T085: Verify citation of real data against approved list."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV data file (e.g., data/raw/real_data.csv)"
    )
    parser.add_argument(
        "--dois",
        type=str,
        default="data/citations/verified_dois.yaml",
        help="Path to the verified DOIs YAML file"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_citation_verification(args.input, args.dois)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except CitationVerificationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
