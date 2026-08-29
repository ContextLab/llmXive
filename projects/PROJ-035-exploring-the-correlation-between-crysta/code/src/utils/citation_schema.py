"""
Citation metadata schema validation module.

Implements pre-validation for citation entries to ensure required fields
exist before processing. This supports Constitution II requirements for
traceable, verifiable research inputs.
"""

from typing import Dict, List, Any, Optional
import logging

# Required fields for a valid citation entry
REQUIRED_CITATION_FIELDS = ['title', 'authors', 'year', 'doi']

# Setup logger for this module
logger = logging.getLogger(__name__)

def validate_citation_entry(entry: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate that a citation entry contains all required fields.
    
    Args:
        entry: Dictionary containing citation metadata
        
    Returns:
        tuple: (is_valid, list_of_missing_fields)
        
    Raises:
        TypeError: If entry is not a dictionary
    """
    if not isinstance(entry, dict):
        raise TypeError("Citation entry must be a dictionary")
    
    missing_fields = []
    for field in REQUIRED_CITATION_FIELDS:
        if field not in entry:
            missing_fields.append(field)
        elif entry[field] is None or (isinstance(entry[field], str) and entry[field].strip() == ""):
            missing_fields.append(field)
    
    is_valid = len(missing_fields) == 0
    return is_valid, missing_fields

def validate_citation_list(citations: List[Dict[str, Any]]) -> tuple[bool, Dict[str, Any]]:
    """
    Validate a list of citation entries.
    
    Args:
        citations: List of dictionaries, each representing a citation entry
        
    Returns:
        tuple: (all_valid, report_dict)
            report_dict contains:
                - total_count: Total number of citations checked
                - valid_count: Number of valid citations
                - invalid_count: Number of invalid citations
                - invalid_entries: List of (index, missing_fields) for invalid entries
    """
    if not isinstance(citations, list):
        raise TypeError("Citations must be a list of dictionaries")
    
    report = {
        'total_count': len(citations),
        'valid_count': 0,
        'invalid_count': 0,
        'invalid_entries': []
    }
    
    for idx, entry in enumerate(citations):
        is_valid, missing = validate_citation_entry(entry)
        if is_valid:
            report['valid_count'] += 1
        else:
            report['invalid_count'] += 1
            report['invalid_entries'].append({
                'index': idx,
                'missing_fields': missing
            })
    
    all_valid = report['invalid_count'] == 0
    return all_valid, report

def get_required_fields() -> List[str]:
    """
    Return the list of required citation fields.
    
    Returns:
        List of field names that must be present in every citation entry
    """
    return REQUIRED_CITATION_FIELDS.copy()

def validate_citation_entry_strict(entry: Dict[str, Any]) -> None:
    """
    Validate a citation entry and raise ValueError if invalid.
    
    This is a strict validation helper that fails loudly on missing fields,
    suitable for pre-validation gates (Constitution II).
    
    Args:
        entry: Dictionary containing citation metadata
        
    Raises:
        ValueError: If any required field is missing or empty
    """
    is_valid, missing = validate_citation_entry(entry)
    if not is_valid:
        raise ValueError(
            f"Citation entry is missing required fields: {missing}. "
            f"Required fields are: {REQUIRED_CITATION_FIELDS}"
        )

def main():
    """
    Command-line entry point for testing citation schema validation.
    
    Runs a simple self-test with sample data to demonstrate functionality.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Running citation schema validation self-test...")
    
    # Test data
    valid_entry = {
        'title': 'Thermal Conductivity in Perovskites',
        'authors': ['Smith, J.', 'Doe, A.'],
        'year': 2021,
        'doi': '10.1038/s41586-021-03456-x'
    }
    
    invalid_entry = {
        'title': 'Incomplete Citation',
        'authors': ['Unknown']
        # Missing 'year' and 'doi'
    }
    
    # Test single entry validation
    is_valid, missing = validate_citation_entry(valid_entry)
    assert is_valid, "Valid entry should pass validation"
    assert len(missing) == 0, "Valid entry should have no missing fields"
    logger.info(f"✓ Valid entry passed: {valid_entry['title']}")
    
    is_valid, missing = validate_citation_entry(invalid_entry)
    assert not is_valid, "Invalid entry should fail validation"
    assert 'year' in missing and 'doi' in missing, "Invalid entry should report missing fields"
    logger.info(f"✓ Invalid entry correctly failed with missing fields: {missing}")
    
    # Test list validation
    citations = [valid_entry, invalid_entry, valid_entry]
    all_valid, report = validate_citation_list(citations)
    
    assert report['total_count'] == 3
    assert report['valid_count'] == 2
    assert report['invalid_count'] == 1
    assert not all_valid
    logger.info(f"✓ List validation report: {report}")
    
    # Test strict validation
    try:
        validate_citation_entry_strict(valid_entry)
        logger.info("✓ Strict validation passed for valid entry")
    except ValueError:
        raise AssertionError("Strict validation should not fail for valid entry")
    
    try:
        validate_citation_entry_strict(invalid_entry)
        raise AssertionError("Strict validation should fail for invalid entry")
    except ValueError as e:
        logger.info(f"✓ Strict validation correctly raised: {str(e)[:80]}...")
    
    logger.info("All self-tests passed successfully!")
    print("Citation schema validation module is functioning correctly.")

if __name__ == "__main__":
    main()
