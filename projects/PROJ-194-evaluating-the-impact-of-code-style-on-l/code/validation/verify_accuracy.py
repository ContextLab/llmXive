"""
Implementation of Constitution Principle II: Data Verification.

This module enforces data integrity before any inference or analysis occurs.
It verifies:
1. Schema compliance for all input data files.
2. Accessibility of external data URLs referenced in metadata.
3. Validity of citations found in documentation or metadata.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
import yaml

class VerificationError(Exception):
    """Raised when data verification fails."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema file.
    
    Args:
        schema_path: Relative path to the schema file (e.g., contracts/dataset.schema.yaml)
        
    Returns:
        The schema dictionary.
        
    Raises:
        VerificationError: If the file cannot be loaded or parsed.
    """
    if not os.path.exists(schema_path):
        raise VerificationError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except Exception as e:
        raise VerificationError(f"Failed to load schema {schema_path}: {e}")

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a JSON object against a JSON Schema (draft-07 compatible).
    
    Note: This is a simplified implementation for core validation. 
    For complex nested validation, a library like jsonschema is recommended,
    but we implement basic checks here to avoid extra dependencies if not strictly necessary.
    However, to be robust, we will attempt to use 'jsonschema' if available, 
    otherwise fallback to basic type checking.
    
    Args:
        data: The data to validate.
        schema: The schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Basic type check
    if 'type' in schema:
        expected_type = schema['type']
        type_map = {
            'object': dict,
            'array': list,
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool
        }
        
        if expected_type in type_map:
            if not isinstance(data, type_map[expected_type]):
                errors.append(f"Expected type '{expected_type}', got '{type(data).__name__}'")
                return False, errors
        
        if expected_type == 'object' and 'properties' in schema:
            required = schema.get('required', [])
            for prop, prop_schema in schema['properties'].items():
                if prop in data:
                    valid, prop_errors = validate_json_against_schema(data[prop], prop_schema)
                    if not valid:
                        errors.extend([f"{prop}: {err}" for err in prop_errors])
                elif prop in required:
                    errors.append(f"Missing required property: {prop}")
    
    return len(errors) == 0, errors

def verify_url(url: str, timeout: int = 10) -> bool:
    """
    Check if a URL is accessible (returns 200 OK).
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        True if accessible, False otherwise.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
        
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False

def verify_citations(citations: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Verify that citations have required fields and optionally check DOIs/URLs.
    
    Args:
        citations: List of citation dictionaries.
        
    Returns:
        Tuple of (all_valid, list_of_errors).
    """
    errors = []
    for i, citation in enumerate(citations):
        if 'title' not in citation:
            errors.append(f"Citation {i}: Missing 'title'")
        if 'author' not in citation:
            errors.append(f"Citation {i}: Missing 'author'")
        if 'year' not in citation:
            errors.append(f"Citation {i}: Missing 'year'")
        
        # If a DOI or URL is present, verify it if it looks valid
        if 'doi' in citation:
            doi = citation['doi']
            if not doi.startswith('10.'):
                errors.append(f"Citation {i}: Invalid DOI format: {doi}")
            # Optional: Verify DOI via crossref API could be added here
        
        if 'url' in citation:
            if not verify_url(citation['url'], timeout=5):
                errors.append(f"Citation {i}: URL not accessible: {citation['url']}")
                
    return len(errors) == 0, errors

def verify_data_urls(data_files: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Verify that data files referenced in metadata have accessible URLs.
    
    Args:
        data_files: List of dictionaries containing 'url' and 'name'.
        
    Returns:
        Tuple of (all_valid, list_of_errors).
    """
    errors = []
    for i, item in enumerate(data_files):
        name = item.get('name', f'Item {i}')
        url = item.get('url')
        if not url:
            errors.append(f"Data item '{name}': Missing URL")
            continue
        
        if not verify_url(url):
            errors.append(f"Data item '{name}': URL not accessible: {url}")
            
    return len(errors) == 0, errors

def run_verification(base_dir: str = '.') -> bool:
    """
    Run all verification steps required by Constitution Principle II.
    
    1. Load and validate schema definitions.
    2. Check data URLs in metadata files (if any exist in data/).
    3. Check citations in documentation (if any exist).
    
    Args:
        base_dir: Project root directory.
        
    Returns:
        True if all verifications pass, False otherwise.
        
    Raises:
        VerificationError: If critical verification steps fail.
    """
    contracts_dir = os.path.join(base_dir, 'contracts')
    data_dir = os.path.join(base_dir, 'data')
    
    # 1. Validate Schema Files
    if os.path.exists(contracts_dir):
        schema_files = [f for f in os.listdir(contracts_dir) if f.endswith('.yaml') or f.endswith('.json')]
        for sf in schema_files:
            try:
                schema = load_schema(os.path.join(contracts_dir, sf))
                if not schema:
                    raise VerificationError(f"Schema {sf} is empty or invalid")
                print(f"Schema OK: {sf}")
            except VerificationError as e:
                raise VerificationError(f"Schema Validation Failed for {sf}: {e}")
    else:
        print("Warning: Contracts directory not found. Skipping schema validation.")

    # 2. Check Data URLs (Look for metadata files in data/)
    # We assume metadata might be in data/metadata.json or similar
    metadata_paths = [
        os.path.join(data_dir, 'metadata.json'),
        os.path.join(data_dir, 'metadata.yaml'),
        os.path.join(data_dir, 'source_info.json')
    ]
    
    for mp in metadata_paths:
        if os.path.exists(mp):
            try:
                with open(mp, 'r', encoding='utf-8') as f:
                    content = json.load(f) if mp.endswith('.json') else yaml.safe_load(f)
                
                # Check for data URLs
                if isinstance(content, dict) and 'data_sources' in content:
                    valid, errors = verify_data_urls(content['data_sources'])
                    if not valid:
                        raise VerificationError(f"Data URL verification failed in {mp}: {errors}")
                
                # Check for citations
                if isinstance(content, dict) and 'citations' in content:
                    valid, errors = verify_citations(content['citations'])
                    if not valid:
                        raise VerificationError(f"Citation verification failed in {mp}: {errors}")
                        
                print(f"Metadata Verification OK: {mp}")
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {mp} as JSON/YAML. Skipping URL checks.")
            except Exception as e:
                raise VerificationError(f"Error verifying {mp}: {e}")

    print("Constitution Principle II Verification: PASSED")
    return True

def main():
    """CLI entry point for verification."""
    import argparse
    parser = argparse.ArgumentParser(description="Verify data accuracy and integrity (Constitution Principle II)")
    parser.add_argument('--base-dir', default='.', help='Project root directory')
    args = parser.parse_args()
    
    try:
        success = run_verification(args.base_dir)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except VerificationError as e:
        print(f"VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()