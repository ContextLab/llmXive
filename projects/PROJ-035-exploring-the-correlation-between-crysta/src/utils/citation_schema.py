"""
Citation Schema Validation Module.

Implements pre-validation for citation metadata entries to ensure
required fields (title, authors, year, doi) are present and valid.
This is a PRE-VALIDATION step per Constitution II.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging

# Required fields for a valid citation entry
REQUIRED_FIELDS: List[str] = ['title', 'authors', 'year', 'doi']

def get_required_fields() -> List[str]:
    """
    Returns the list of required fields for citation metadata.

    Returns:
        List[str]: The required field names.
    """
    return REQUIRED_FIELDS.copy()

def _validate_field_presence(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Checks if all required fields are present in the citation entry.

    Args:
        entry: The citation dictionary to validate.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_missing_fields)
    """
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in entry or entry[field] is None:
            missing.append(field)
        elif isinstance(entry[field], str) and entry[field].strip() == "":
            missing.append(field)
    
    return len(missing) == 0, missing

def _validate_field_types(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that fields have appropriate types.

    Args:
        entry: The citation dictionary to validate.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_type_errors)
    """
    errors = []
    
    # title must be a non-empty string
    if 'title' in entry and entry['title'] is not None:
        if not isinstance(entry['title'], str) or entry['title'].strip() == "":
            errors.append("title must be a non-empty string")
    
    # authors must be a list of strings or a non-empty string
    if 'authors' in entry and entry['authors'] is not None:
        if isinstance(entry['authors'], list):
            if len(entry['authors']) == 0:
                errors.append("authors list cannot be empty")
            elif not all(isinstance(a, str) and a.strip() != "" for a in entry['authors']):
                errors.append("all authors must be non-empty strings")
        elif isinstance(entry['authors'], str):
            if entry['authors'].strip() == "":
                errors.append("authors string cannot be empty")
        else:
            errors.append("authors must be a list or string")
    
    # year must be an integer or a string representing an integer
    if 'year' in entry and entry['year'] is not None:
        year_val = entry['year']
        if isinstance(year_val, int):
            if year_val < 1000 or year_val > 9999:
                errors.append("year must be a valid 4-digit year")
        elif isinstance(year_val, str):
            try:
                y = int(year_val)
                if y < 1000 or y > 9999:
                    errors.append("year string must represent a valid 4-digit year")
            except ValueError:
                errors.append("year string must be convertible to integer")
        else:
            errors.append("year must be an integer or string")
    
    # doi must be a non-empty string
    if 'doi' in entry and entry['doi'] is not None:
        if not isinstance(entry['doi'], str) or entry['doi'].strip() == "":
            errors.append("doi must be a non-empty string")
    
    return len(errors) == 0, errors

def validate_citation_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a single citation entry for required fields and basic format.

    Args:
        entry: A dictionary containing citation metadata.

    Returns:
        Dict[str, Any]: A validation result with keys:
            - 'valid': bool indicating if the entry is valid
            - 'errors': list of error messages (empty if valid)
            - 'missing_fields': list of missing required fields
    """
    result = {
        'valid': True,
        'errors': [],
        'missing_fields': []
    }

    # Check presence of required fields
    has_fields, missing = _validate_field_presence(entry)
    if not has_fields:
        result['valid'] = False
        result['missing_fields'] = missing
        result['errors'].extend([f"Missing required field: {f}" for f in missing])

    # Check field types and formats
    if has_fields:
        has_types, type_errors = _validate_field_types(entry)
        if not has_types:
            result['valid'] = False
            result['errors'].extend(type_errors)

    return result

def validate_citation_entry_strict(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strict validation that includes DOI format checking.

    Args:
        entry: A dictionary containing citation metadata.

    Returns:
        Dict[str, Any]: A validation result with keys:
            - 'valid': bool indicating if the entry is valid
            - 'errors': list of error messages (empty if valid)
            - 'missing_fields': list of missing required fields
    """
    result = validate_citation_entry(entry)
    
    if result['valid'] and 'doi' in entry and entry['doi'] is not None:
        doi = str(entry['doi']).strip()
        # Basic DOI format check: should start with 10. and contain /
        if not doi.startswith('10.') or '/' not in doi:
            result['valid'] = False
            result['errors'].append("doi must be in valid DOI format (e.g., 10.xxxx/xxxxx)")
    
    return result

def validate_citation_list(citations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates a list of citation entries.

    Args:
        citations: A list of citation dictionaries.

    Returns:
        Dict[str, Any]: A validation result with keys:
            - 'valid': bool indicating if all entries are valid
            - 'total': total number of citations
            - 'valid_count': number of valid citations
            - 'invalid_count': number of invalid citations
            - 'errors': list of dictionaries with 'index' and 'errors' for invalid entries
    """
    result = {
        'valid': True,
        'total': len(citations),
        'valid_count': 0,
        'invalid_count': 0,
        'errors': []
    }

    for i, entry in enumerate(citations):
        validation = validate_citation_entry(entry)
        if validation['valid']:
            result['valid_count'] += 1
        else:
            result['valid'] = False
            result['invalid_count'] += 1
            result['errors'].append({
                'index': i,
                'errors': validation['errors'],
                'missing_fields': validation['missing_fields']
            })

    return result

def main():
    """
    Command-line entry point for citation schema validation.
    Expects a JSON file path as argument.
    """
    import sys
    import json
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python citation_schema.py <citations.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    try:
        with open(input_path, 'r') as f:
            citations = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)

    if not isinstance(citations, list):
        print("Error: Input must be a JSON array of citation objects")
        sys.exit(1)

    result = validate_citation_list(citations)
    
    print(f"Citation Validation Report:")
    print(f"  Total entries: {result['total']}")
    print(f"  Valid: {result['valid_count']}")
    print(f"  Invalid: {result['invalid_count']}")
    
    if result['errors']:
        print("\nInvalid entries:")
        for err in result['errors']:
            print(f"  [{err['index']}]: {', '.join(err['errors'])}")
            if err['missing_fields']:
                print(f"      Missing fields: {', '.join(err['missing_fields'])}")
    
    sys.exit(0 if result['valid'] else 1)

if __name__ == "__main__":
    main()
