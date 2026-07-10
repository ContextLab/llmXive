"""
Utility functions for the narrative perspective research pipeline.

This module provides helper functions for data hygiene, hashing, and
other common operations required by the pipeline and CI agents.
"""

import re
import hashlib
from typing import Optional, List


def scan_for_pii(text: str) -> List[str]:
    """
    Detects potential Personally Identifiable Information (PII) in the provided text.

    This function is intended to be invoked by the CI Repository-Hygiene Agent
    as a blocking gate (Constitution Principle III) to prevent accidental
    leakage of sensitive data in research artifacts.

    It scans for:
    - Email addresses
    - US Phone numbers (various formats)
    - US Social Security Numbers (SSN)
    - Credit Card numbers (basic Luhn-adjacent pattern matching for 13-19 digits)
    - IP addresses (IPv4)

    Args:
        text (str): The text content to scan.

    Returns:
        List[str]: A list of strings representing the detected PII patterns.
                   Returns an empty list if no PII is found.
    """
    found_pii = []

    # 1. Email addresses
    # Matches standard email format: local@domain.tld
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    found_pii.extend(emails)

    # 2. US Phone Numbers
    # Matches formats like: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    phone_pattern = r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    found_pii.extend(phones)

    # 3. Social Security Numbers (SSN)
    # Matches format: XXX-XX-XXXX
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    ssns = re.findall(ssn_pattern, text)
    found_pii.extend(ssns)

    # 4. Credit Card Numbers
    # Matches 13 to 19 digit sequences, often with spaces or dashes
    # This is a heuristic pattern; real validation would require Luhn algorithm
    cc_pattern = r'\b(?:\d[ -]*?){13,19}\b'
    # Refine: ensure it's mostly digits and length is appropriate
    potential_cc = re.findall(cc_pattern, text)
    for match in potential_cc:
        digits_only = re.sub(r'\D', '', match)
        if 13 <= len(digits_only) <= 19:
            found_pii.append(match.strip())

    # 5. IPv4 Addresses
    # Matches standard dotted decimal notation
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    ips = re.findall(ip_pattern, text)
    found_pii.extend(ips)

    # Remove duplicates while preserving order
    seen = set()
    unique_pii = []
    for item in found_pii:
        if item not in seen:
            seen.add(item)
            unique_pii.append(item)

    return unique_pii


def compute_artifact_hash(file_path: str) -> str:
    """
    Computes the SHA-256 hash of a file for versioning and integrity checks.

    This function is intended to be invoked by the Advancement-Evaluator Agent
    (Constitution Principle V) to verify artifact consistency.

    Args:
        file_path (str): The absolute or relative path to the file.

    Returns:
        str: The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading artifact file {file_path}: {e}")