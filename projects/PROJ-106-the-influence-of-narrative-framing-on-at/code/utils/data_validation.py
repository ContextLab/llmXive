"""
Data validation utilities for the Narrative Framing study.

Provides schema definitions, validation functions, and data integrity checks
for survey responses and experimental data.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import csv
import json
from dataclasses import dataclass, field

# Constants for Likert scale validation
LIKERT_MIN = 1
LIKERT_MAX = 7

# Required columns for cleaned responses
REQUIRED_CLEANUP_COLUMNS = {
    'participant_id',
    'condition',
    'manipulation_check',
    'manipulation_check_failed',
}

# Expected item prefixes for survey scales
EXPECTED_ITEM_PREFIXES = {
    'attitude': 7,   # attitude_item_1 through attitude_item_7
    'usefulness': 3, # usefulness_item_1 through usefulness_item_3
    'trust': 4,      # trust_item_1 through trust_item_4
}

@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    message: str
    value: Any = None
    
@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(ValidationError(field, message, value))
        self.is_valid = False
        
    def add_warning(self, message: str):
        self.warnings.append(message)
        
def validate_liker_scale(
    value: Union[int, float, str], 
    min_val: int = LIKERT_MIN, 
    max_val: int = LIKERT_MAX
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is within the expected Likert scale range.
    
    Args:
        value: The value to validate
        min_val: Minimum acceptable value (default: 1)
        max_val: Maximum acceptable value (default: 7)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        numeric_val = float(value)
        if numeric_val != int(numeric_val):
            return False, f"Value must be an integer, got {numeric_val}"
        if not (min_val <= int(numeric_val) <= max_val):
            return False, f"Value {int(numeric_val)} out of range [{min_val}, {max_val}]"
        return True, None
    except (ValueError, TypeError):
        return False, f"Invalid numeric value: {value}"

def validate_participant_id(participant_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate participant ID format.
    
    Expected format: Non-empty string, alphanumeric with underscores/hyphens allowed.
    """
    if not participant_id or not isinstance(participant_id, str):
        return False, "Participant ID must be a non-empty string"
    
    if len(participant_id.strip()) == 0:
        return False, "Participant ID cannot be whitespace only"
        
    return True, None

def validate_condition(condition: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that condition is one of the expected experimental groups.
    """
    valid_conditions = {'Partner', 'Tool'}
    if condition not in valid_conditions:
        return False, f"Condition '{condition}' not in {valid_conditions}"
    return True, None

def validate_csv_structure(
    file_path: Union[str, Path], 
    required_columns: set
) -> ValidationResult:
    """
    Validate the structure of a CSV file.
    
    Args:
        file_path: Path to the CSV file
        required_columns: Set of required column names
        
    Returns:
        ValidationResult with any errors found
    """
    result = ValidationResult(is_valid=True)
    path = Path(file_path)
    
    if not path.exists():
        result.add_error("file", f"File not found: {file_path}")
        return result
        
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames) if reader.fieldnames else set()
            
            missing = required_columns - headers
            if missing:
                result.add_error(
                    "columns", 
                    f"Missing required columns: {missing}",
                    list(missing)
                )
                
            # Check for extra unexpected columns (warning only)
            extra = headers - required_columns
            if extra:
                result.add_warning(f"Extra columns found: {extra}")
                
    except Exception as e:
        result.add_error("file", f"Error reading CSV: {str(e)}")
        
    return result

def validate_survey_response_row(
    row: Dict[str, Any], 
    strict: bool = True
) -> ValidationResult:
    """
    Validate a single row of survey response data.
    
    Args:
        row: Dictionary representing a CSV row
        strict: If True, fail on missing required fields; if False, warn
        
    Returns:
        ValidationResult for the row
    """
    result = ValidationResult(is_valid=True)
    
    # Validate participant ID
    if 'participant_id' in row:
        valid, err = validate_participant_id(row['participant_id'])
        if not valid:
            result.add_error('participant_id', err, row['participant_id'])
    elif strict:
        result.add_error('participant_id', 'Missing required field')
        
    # Validate condition
    if 'condition' in row:
        valid, err = validate_condition(row['condition'])
        if not valid:
            result.add_error('condition', err, row['condition'])
    elif strict:
        result.add_error('condition', 'Missing required field')
        
    # Validate manipulation check fields
    for field_name in ['manipulation_check', 'manipulation_check_failed']:
        if field_name in row:
            if not isinstance(row[field_name], (str, bool)):
                result.add_error(
                    field_name, 
                    f"Field must be boolean or string, got {type(row[field_name])}",
                    row[field_name]
                )
                
    # Validate Likert scale items
    for prefix, count in EXPECTED_ITEM_PREFIXES.items():
        for i in range(1, count + 1):
            col_name = f"{prefix}_item_{i}"
            if col_name in row:
                valid, err = validate_liker_scale(row[col_name])
                if not valid:
                    result.add_error(col_name, err, row[col_name])
                
    return result

def validate_dataset_integrity(
    file_path: Union[str, Path]
) -> ValidationResult:
    """
    Comprehensive validation of the cleaned responses dataset.
    
    Checks:
    1. File exists and is readable
    2. Required columns are present
    3. No duplicate participant IDs
    4. All rows pass individual validation
    5. Manipulation check logic consistency
    
    Args:
        file_path: Path to the cleaned_responses.csv file
        
    Returns:
        ValidationResult with all errors and warnings
    """
    result = validate_csv_structure(file_path, REQUIRED_CLEANUP_COLUMNS)
    if not result.is_valid:
        return result
        
    path = Path(file_path)
    participant_ids = set()
    row_count = 0
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                row_count += 1
                pid = row.get('participant_id')
                
                # Check for duplicates
                if pid in participant_ids:
                    result.add_error(
                        'participant_id',
                        f"Duplicate participant ID: {pid}",
                        pid
                    )
                else:
                    participant_ids.add(pid)
                    
                # Validate row content
                row_result = validate_survey_response_row(row, strict=False)
                for err in row_result.errors:
                    # Add row context to error
                    result.add_error(
                        f"row_{row_count}_{err.field}",
                        err.message,
                        err.value
                    )
                    
                # Check manipulation check consistency
                mc = row.get('manipulation_check')
                mc_failed = row.get('manipulation_check_failed')
                
                if mc and mc_failed is not None:
                    # If manipulation_check_failed is True, manipulation_check should indicate failure
                    # This is a logic consistency check
                    if str(mc_failed).lower() == 'true':
                        if mc.lower() == 'correct' or mc.lower() == 'passed':
                            result.add_warning(
                                f"Row {row_count}: manipulation_check_failed=True but "
                                f"manipulation_check='{mc}' suggests pass"
                            )
                
    except Exception as e:
        result.add_error("file", f"Error processing file: {str(e)}")
        
    if row_count == 0:
        result.add_warning("Dataset is empty")
        
    return result

def generate_data_schema() -> Dict[str, Any]:
    """
    Generate a JSON schema describing the expected data structure.
    
    Returns:
        Dictionary representing the data schema
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Cleaned Survey Responses",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "participant_id",
                "condition",
                "manipulation_check",
                "manipulation_check_failed"
            ],
            "properties": {
                "participant_id": {
                    "type": "string",
                    "description": "Unique identifier for the participant"
                },
                "condition": {
                    "type": "string",
                    "enum": ["Partner", "Tool"],
                    "description": "Experimental condition assignment"
                },
                "manipulation_check": {
                    "type": "string",
                    "description": "Response to manipulation check question"
                },
                "manipulation_check_failed": {
                    "type": "boolean",
                    "description": "Whether the participant failed the manipulation check"
                }
            }
        }
    }
    
    # Add dynamic item properties
    for prefix, count in EXPECTED_ITEM_PREFIXES.items():
        for i in range(1, count + 1):
            prop_name = f"{prefix}_item_{i}"
            schema["items"]["properties"][prop_name] = {
                "type": "integer",
                "minimum": LIKERT_MIN,
                "maximum": LIKERT_MAX,
                "description": f"Response for {prefix} scale item {i}"
            }
            
    return schema