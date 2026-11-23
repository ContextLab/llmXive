"""
Verification module for Constitution Principle II.

Enforces data integrity by verifying citations, checking data URLs,
and validating JSON data against defined schema contracts before
any inference or analysis is performed.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Schema validation logic (simple implementation without external libs like jsonschema)
def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a file.
    
    Args:
        schema_path: Path to the schema file (relative to project root).
        
    Returns:
        The schema dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema file is not valid JSON.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a JSON object against a simple schema definition.
    
    Supports 'type', 'required', 'properties', and 'items' (for lists).
    This is a lightweight validator to avoid heavy dependencies.
    
    Args:
        data: The JSON object to validate.
        schema: The schema definition.
        
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []
    
    # Check type
    if 'type' in schema:
        expected_type = schema['type']
        if expected_type == 'object' and not isinstance(data, dict):
            errors.append(f"Expected object, got {type(data).__name__}")
            return False, errors
        elif expected_type == 'array' and not isinstance(data, list):
            errors.append(f"Expected array, got {type(data).__name__}")
            return False, errors
        elif expected_type == 'string' and not isinstance(data, str):
            errors.append(f"Expected string, got {type(data).__name__}")
            return False, errors
        elif expected_type == 'integer' and not isinstance(data, int):
            errors.append(f"Expected integer, got {type(data).__name__}")
            return False, errors
        elif expected_type == 'number' and not isinstance(data, (int, float)):
            errors.append(f"Expected number, got {type(data).__name__}")
            return False, errors
        elif expected_type == 'boolean' and not isinstance(data, bool):
            errors.append(f"Expected boolean, got {type(data).__name__}")
            return False, errors
    
    # Check required fields for objects
    if isinstance(data, dict) and 'required' in schema:
        for field in schema['required']:
            if field not in data:
                errors.append(f"Missing required field: {field}")
    
    # Check properties
    if isinstance(data, dict) and 'properties' in schema:
        for key, value in data.items():
            if key in schema['properties']:
                prop_schema = schema['properties'][key]
                valid, prop_errors = validate_json_against_schema(value, prop_schema)
                if not valid:
                    errors.extend([f"Field '{key}': {e}" for e in prop_errors])
            elif 'additionalProperties' in schema and not schema['additionalProperties']:
                errors.append(f"Unexpected field: {key}")
    
    # Check items for arrays
    if isinstance(data, list) and 'items' in schema:
        item_schema = schema['items']
        for i, item in enumerate(data):
            valid, item_errors = validate_json_against_schema(item, item_schema)
            if not valid:
                errors.extend([f"Item {i}: {e}" for e in item_errors])
    
    return len(errors) == 0, errors

def verify_url(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Verifies that a URL is accessible and returns a valid HTTP status.
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    if not url.startswith(('http://', 'https://')):
        return False, f"Invalid URL scheme: {url}"
    
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True, None
            else:
                return False, f"URL returned status {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def verify_citations(citations: List[Dict[str, Any]], schema_path: str) -> Tuple[bool, List[str]]:
    """
    Verifies citation data against a schema and checks internal consistency.
    
    Args:
        citations: List of citation dictionaries.
        schema_path: Path to the citation schema.
        
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load citation schema: {str(e)}"]
    
    for i, citation in enumerate(citations):
        valid, prop_errors = validate_json_against_schema(citation, schema)
        if not valid:
            errors.extend([f"Citation {i}: {e}" for e in prop_errors])
        
        # Additional consistency checks
        if 'url' in citation:
            is_valid, err = verify_url(citation['url'])
            if not is_valid:
                errors.append(f"Citation {i} URL invalid: {err}")
        
        if 'title' not in citation and 'url' not in citation:
            errors.append(f"Citation {i} must have at least a title or URL")
    
    return len(errors) == 0, errors

def verify_data_urls(data_entries: List[Dict[str, Any]], schema_path: str) -> Tuple[bool, List[str]]:
    """
    Verifies data entries and ensures all referenced URLs are accessible.
    
    Args:
        data_entries: List of data entry dictionaries.
        schema_path: Path to the data schema.
        
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load data schema: {str(e)}"]
    
    for i, entry in enumerate(data_entries):
        valid, prop_errors = validate_json_against_schema(entry, schema)
        if not valid:
            errors.extend([f"Entry {i}: {e}" for e in prop_errors])
        
        # Check for URL fields in the entry
        # Common fields that might contain URLs
        url_fields = ['source_url', 'data_url', 'download_url', 'url', 'link']
        for field in url_fields:
            if field in entry:
                value = entry[field]
                if isinstance(value, str):
                    is_valid, err = verify_url(value)
                    if not is_valid:
                        errors.append(f"Entry {i} field '{field}' URL invalid: {err}")
                elif isinstance(value, list):
                    for j, url in enumerate(value):
                        if isinstance(url, str):
                            is_valid, err = verify_url(url)
                            if not is_valid:
                                errors.append(f"Entry {i} field '{field}' URL {j} invalid: {err}")
    
    return len(errors) == 0, errors

class VerificationError(Exception):
    """Exception raised when verification fails."""
    pass

def run_verification(
    citations_path: Optional[str] = None,
    citations_schema_path: str = "contracts/citation.schema.yaml",
    data_path: Optional[str] = None,
    data_schema_path: str = "contracts/dataset.schema.yaml",
    strict: bool = True
) -> Dict[str, Any]:
    """
    Runs the full verification suite for Constitution Principle II.
    
    Args:
        citations_path: Path to the citations JSON file.
        citations_schema_path: Path to the citations schema.
        data_path: Path to the data JSON file.
        data_schema_path: Path to the data schema.
        strict: If True, raises an error on any verification failure.
        
    Returns:
        A dictionary with verification results.
        
    Raises:
        VerificationError: If strict mode is enabled and verification fails.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "citations_valid": False,
        "data_valid": False,
        "errors": [],
        "warnings": []
    }
    
    # Verify Citations
    if citations_path and os.path.exists(citations_path):
        try:
            with open(citations_path, 'r', encoding='utf-8') as f:
                citations = json.load(f)
            
            is_valid, errors = verify_citations(citations, citations_schema_path)
            results["citations_valid"] = is_valid
            if errors:
                results["errors"].extend(errors)
        except Exception as e:
            error_msg = f"Failed to verify citations: {str(e)}"
            results["errors"].append(error_msg)
            if strict:
                raise VerificationError(error_msg)
    else:
        results["warnings"].append("No citations file found or provided")
    
    # Verify Data URLs
    if data_path and os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list and dict with 'data' key
            if isinstance(data, dict) and 'data' in data:
                entries = data['data']
            elif isinstance(data, list):
                entries = data
            else:
                entries = [data]
            
            is_valid, errors = verify_data_urls(entries, data_schema_path)
            results["data_valid"] = is_valid
            if errors:
                results["errors"].extend(errors)
        except Exception as e:
            error_msg = f"Failed to verify data URLs: {str(e)}"
            results["errors"].append(error_msg)
            if strict:
                raise VerificationError(error_msg)
    else:
        results["warnings"].append("No data file found or provided")
    
    # Overall status
    results["overall_valid"] = results["citations_valid"] and results["data_valid"]
    
    if strict and not results["overall_valid"]:
        raise VerificationError(f"Verification failed: {len(results['errors'])} errors found")
    
    return results

def main():
    """
    Command-line entry point for verification.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify data accuracy and citations (Constitution Principle II)")
    parser.add_argument("--citations", type=str, help="Path to citations JSON file")
    parser.add_argument("--data", type=str, help="Path to data JSON file")
    parser.add_argument("--citations-schema", type=str, default="contracts/citation.schema.yaml", help="Path to citations schema")
    parser.add_argument("--data-schema", type=str, default="contracts/dataset.schema.yaml", help="Path to data schema")
    parser.add_argument("--no-strict", action="store_true", help="Do not raise error on failure")
    
    args = parser.parse_args()
    
    try:
        results = run_verification(
            citations_path=args.citations,
            citations_schema_path=args.citations_schema,
            data_path=args.data,
            data_schema_path=args.data_schema,
            strict=not args.no_strict
        )
        
        print("Verification Results:")
        print(f"  Timestamp: {results['timestamp']}")
        print(f"  Citations Valid: {results['citations_valid']}")
        print(f"  Data Valid: {results['data_valid']}")
        print(f"  Overall Valid: {results['overall_valid']}")
        
        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for err in results['errors']:
                print(f"  - {err}")
        
        if results['warnings']:
            print(f"\nWarnings ({len(results['warnings'])}):")
            for warn in results['warnings']:
                print(f"  - {warn}")
        
        if results['overall_valid']:
            print("\n✅ Verification PASSED")
            sys.exit(0)
        else:
            print("\n❌ Verification FAILED")
            sys.exit(1)
            
    except VerificationError as e:
        print(f"\n❌ Verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()