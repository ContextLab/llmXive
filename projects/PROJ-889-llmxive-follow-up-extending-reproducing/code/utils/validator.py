"""
Validation utilities for data integrity and source verification.

This module provides functions to validate trajectory data against JSON schemas
and to verify the authenticity of external data sources (e.g., arXiv papers).
"""
import json
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from jsonschema import validate, ValidationError

from code.config import get_project_root
from code.utils.io_utils import read_json


# Constants
ARXIV_API_URL = "https://export.arxiv.org/api/query"
VALID_ARXIV_PATTERN = re.compile(r'^\d{4}\.\d{5}$')


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'trajectory_schema.json')

    Returns:
        The loaded schema as a dictionary.
    """
    root = get_project_root()
    schema_path = root / "contracts" / schema_name

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    return read_json(str(schema_path))


def validate_trajectory_data(data: Dict[str, Any]) -> bool:
    """
    Validate trajectory data against the trajectory schema.

    Args:
        data: The trajectory data to validate.

    Returns:
        True if valid.

    Raises:
        ValidationError: If the data does not match the schema.
    """
    schema = load_schema("trajectory_schema.json")
    validate(instance=data, schema=schema)
    return True


def validate_metrics_data(data: Dict[str, Any]) -> bool:
    """
    Validate metrics data against the metrics schema.

    Args:
        data: The metrics data to validate.

    Returns:
        True if valid.

    Raises:
        ValidationError: If the data does not match the schema.
    """
    schema = load_schema("metrics_schema.json")
    validate(instance=data, schema=schema)
    return True


def validate_file_against_schema(file_path: str, schema_name: str) -> bool:
    """
    Validate a JSON file against a specific schema.

    Args:
        file_path: Path to the JSON file.
        schema_name: Name of the schema file in contracts/.

    Returns:
        True if valid.

    Raises:
        FileNotFoundError: If file or schema not found.
        ValidationError: If validation fails.
    """
    data = read_json(file_path)
    schema = load_schema(schema_name)
    validate(instance=data, schema=schema)
    return True


def validate_cherrl_source(arxiv_id: str) -> bool:
    """
    Validate that the provided arXiv ID corresponds to the CHERRL paper.

    This function performs a "fail loud" check:
    1. Verifies the format of the arXiv ID.
    2. Queries the arXiv API.
    3. Verifies the returned paper ID matches the requested ID.
    4. (Optional) Verifies the title contains "CHERRL" or similar keywords.

    If validation fails for any reason, it logs an error and exits with code 2.

    Args:
        arxiv_id: The arXiv ID to validate (e.g., '2606.04923').

    Returns:
        True if validation succeeds.

    Raises:
        SystemExit: With code 2 on any validation failure.
    """
    # 1. Format Check
    if not VALID_ARXIV_PATTERN.match(arxiv_id):
        print(f"ERROR: Invalid arXiv ID format: '{arxiv_id}'. Expected format: YYYY.NNNNN", file=sys.stderr)
        sys.exit(2)

    # 2. Query arXiv API
    url = f"{ARXIV_API_URL}?id_list={arxiv_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Failed to connect to arXiv API: {e}", file=sys.stderr)
        sys.exit(2)

    # 3. Parse Response
    try:
        # arXiv API returns Atom XML by default, but we can request JSON via specific headers or parsing XML.
        # The standard API returns Atom. Let's parse the XML simply or use a library.
        # For simplicity and dependency minimization, we'll assume the API returns XML and parse it.
        # However, the prompt implies using standard libraries.
        # Let's try to fetch as text and parse.
        # Actually, arXiv API default is Atom.
        # To avoid adding lxml/etree complexity if not needed, let's check if we can get JSON.
        # arXiv API doesn't natively support JSON directly without custom headers in some versions,
        # but standard practice is XML.
        # Let's use xml.etree.ElementTree which is standard.
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        # Define namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }

        # Find the entry
        entry = root.find('atom:entry', ns)
        if entry is None:
            print("ERROR: No entry found in arXiv response.", file=sys.stderr)
            sys.exit(2)

        # Extract ID and Title
        id_elem = entry.find('atom:id', ns)
        title_elem = entry.find('atom:title', ns)

        if id_elem is None or title_elem is None:
            print("ERROR: Could not extract ID or Title from arXiv response.", file=sys.stderr)
            sys.exit(2)

        paper_id = id_elem.text.split('/')[-1]
        title = title_elem.text.strip()

    except ET.ParseError as e:
        print(f"ERROR: Failed to parse arXiv response XML: {e}", file=sys.stderr)
        sys.exit(2)

    # 4. Verify ID Match
    if paper_id != arxiv_id:
        print(f"ERROR: arXiv ID mismatch. Requested: {arxiv_id}, Found: {paper_id}", file=sys.stderr)
        sys.exit(2)

    # 5. Verify Content (Basic check for "CHERRL" in title)
    if "CHERRL" not in title.upper():
        print(f"ERROR: Paper title does not contain 'CHERRL'. Title: {title}", file=sys.stderr)
        sys.exit(2)

    print(f"SUCCESS: Validated CHERRL source arXiv:{arxiv_id} - '{title}'")
    return True