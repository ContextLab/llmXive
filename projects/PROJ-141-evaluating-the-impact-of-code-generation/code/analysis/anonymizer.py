"""
Anonymization module for participant data.

Implements Constitution VII compliance:
- Removes PII fields (name, email, IP address)
- Replaces participant_id with SHA-256 hash
- Operates on dictionaries representing participant records
"""
import hashlib
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Standard PII field names to remove
PII_FIELDS = [
    'name', 'full_name', 'first_name', 'last_name',
    'email', 'email_address', 'e_mail',
    'ip_address', 'ip', 'ip_addr', 'client_ip',
    'phone', 'phone_number', 'address', 'street_address',
    'ssn', 'social_security', 'birth_date', 'date_of_birth',
    'credit_card', 'card_number', 'password', 'pin'
]

# Regex patterns for detecting PII in other fields
PII_PATTERNS = [
    (re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'), 'email'),  # Email pattern
    (re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$'), 'ip_address'),  # IPv4 pattern
    (re.compile(r'^\+?\d[\d\s-]{8,}\d$'), 'phone'),  # Phone pattern
]

def generate_anonymous_id(participant_id: str, salt: Optional[str] = None) -> str:
    """
    Generate a deterministic anonymous ID from a participant ID using SHA-256.
    
    Args:
        participant_id: The original participant identifier
        salt: Optional salt for additional security (defaults to project constant)
    
    Returns:
        Hex-encoded SHA-256 hash string
    """
    if salt is None:
        salt = "llmXive_project_salt_constitution_vii"
    
    combined = f"{salt}:{participant_id}"
    hash_object = hashlib.sha256(combined.encode('utf-8'))
    return hash_object.hexdigest()

def is_pii_field(field_name: str) -> bool:
    """
    Check if a field name matches known PII patterns.
    
    Args:
        field_name: The field name to check
    
    Returns:
        True if the field is likely PII, False otherwise
    """
    field_lower = field_name.lower().strip()
    return field_lower in PII_FIELDS

def detect_pii_value(value: Any) -> bool:
    """
    Detect if a value contains PII based on pattern matching.
    
    Args:
        value: The value to check
    
    Returns:
        True if the value appears to be PII, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    for pattern, p_type in PII_PATTERNS:
        if pattern.match(value):
            return True
    return False

def anonymize_record(record: Dict[str, Any], salt: Optional[str] = None) -> Dict[str, Any]:
    """
    Anonymize a single participant record.
    
    - Removes fields identified as PII
    - Replaces participant_id with SHA-256 hash
    - Returns a new dictionary with anonymized data
    
    Args:
        record: Dictionary containing participant data
        salt: Optional salt for ID hashing
    
    Returns:
        Anonymized dictionary
    """
    if not isinstance(record, dict):
        raise TypeError("Record must be a dictionary")
    
    anonymized = {}
    
    for key, value in record.items():
        # Skip PII fields
        if is_pii_field(key):
            continue
        
        # Skip fields with PII values
        if detect_pii_value(value):
            continue
        
        # Transform participant_id
        if key == 'participant_id' or key == 'id':
            anonymized['anonymous_id'] = generate_anonymous_id(str(value), salt)
            continue
        
        # Keep other fields
        anonymized[key] = value
    
    return anonymized

def anonymize_dataset(records: List[Dict[str, Any]], salt: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Anonymize a list of participant records.
    
    Args:
        records: List of dictionaries containing participant data
        salt: Optional salt for ID hashing
    
    Returns:
        List of anonymized dictionaries
    """
    return [anonymize_record(record, salt) for record in records]

def get_anonymization_report(original: Dict[str, Any], anonymized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a report of what was removed or transformed.
    
    Args:
        original: Original record
        anonymized: Anonymized record
    
    Returns:
        Dictionary with statistics about the anonymization process
    """
    removed_fields = [k for k in original.keys() if k not in anonymized and k != 'anonymous_id']
    transformed_fields = ['participant_id' if 'participant_id' in original else 'id' 
                          if 'id' in original else None]
    transformed_fields = [f for f in transformed_fields if f]
    
    return {
        'total_fields_original': len(original),
        'total_fields_anonymized': len(anonymized),
        'removed_fields': removed_fields,
        'transformed_fields': transformed_fields,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def main():
    """
    Command-line interface for testing anonymization.
    Reads from data/ if available, otherwise uses sample data.
    """
    import json
    import sys
    from pathlib import Path
    
    # Sample test data
    test_record = {
        'participant_id': 'P-12345',
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'ip_address': '192.168.1.100',
        'age': 28,
        'programming_experience_years': 5,
        'condition': 'LLM-assisted',
        'session_count': 3,
        'timestamp': '2024-01-15T10:30:00Z'
    }
    
    print("Original Record:")
    print(json.dumps(test_record, indent=2))
    
    anonymized = anonymize_record(test_record)
    
    print("\nAnonymized Record:")
    print(json.dumps(anonymized, indent=2))
    
    report = get_anonymization_report(test_record, anonymized)
    
    print("\nAnonymization Report:")
    print(json.dumps(report, indent=2))
    
    # Verify no PII remains
    pii_detected = False
    for key, value in anonymized.items():
        if is_pii_field(key) or detect_pii_value(value):
            print(f"ERROR: PII detected in anonymized record: {key} = {value}")
            pii_detected = True
    
    if not pii_detected:
        print("\n✓ Anonymization successful: No PII detected in output.")
    
    return 0 if not pii_detected else 1

if __name__ == '__main__':
    sys.exit(main())
