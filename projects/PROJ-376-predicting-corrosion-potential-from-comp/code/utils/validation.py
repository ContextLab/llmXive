"""
Schema validation utilities for the corrosion potential prediction pipeline.

This module provides functions to enforce non-null constraints and validate
data records against defined schemas.
"""
from typing import Dict, Any, List, Optional, Set, Type
from dataclasses import fields, is_dataclass
from utils.exceptions import SchemaMismatchError, DataInsufficientError
from utils.logging import get_logger

logger = get_logger(__name__)


def validate_non_nulls(
    records: List[Any],
    schema_fields: Optional[Set[str]] = None,
    record_type: Optional[Type] = None
) -> int:
    """
    Validate that critical fields in a list of records are non-null.
    
    Args:
        records: List of dataclass instances or dictionaries to validate.
        schema_fields: Optional set of field names that must be non-null.
                       If None, all fields of the dataclass type are checked.
        record_type: Optional dataclass type to infer fields if records are empty.
    
    Returns:
        int: Number of valid records (all critical fields non-null).
    
    Raises:
        SchemaMismatchError: If records contain null values in critical fields.
        DataInsufficientError: If no valid records remain after validation.
    """
    if not records:
        logger.warning("Empty record list provided to validation")
        raise DataInsufficientError("No records provided for validation")
    
    valid_count = 0
    invalid_indices = []
    invalid_details = []
    
    # Determine which fields to check
    check_fields = schema_fields
    if check_fields is None:
        # Infer from the first record if it's a dataclass
        first_record = records[0]
        if is_dataclass(first_record) and not isinstance(first_record, type):
            check_fields = {f.name for f in fields(first_record)}
        elif isinstance(first_record, dict):
            check_fields = set(first_record.keys())
        elif record_type is not None and is_dataclass(record_type):
            check_fields = {f.name for f in fields(record_type)}
        else:
            # Cannot infer fields, skip validation but log warning
            logger.warning("Could not infer schema fields; skipping non-null validation")
            return len(records)
    
    for idx, record in enumerate(records):
        has_null = False
        null_fields = []
        
        if is_dataclass(record) and not isinstance(record, type):
            # Dataclass instance
            record_dict = {f.name: getattr(record, f.name) for f in fields(record)}
        elif isinstance(record, dict):
            record_dict = record
        else:
            logger.warning(f"Record at index {idx} is not a dataclass or dict; skipping")
            continue
        
        for field_name in check_fields:
            value = record_dict.get(field_name)
            if value is None:
                has_null = True
                null_fields.append(field_name)
        
        if has_null:
            invalid_indices.append(idx)
            invalid_details.append({
                "index": idx,
                "null_fields": null_fields
            })
        else:
            valid_count += 1
    
    if invalid_details:
        logger.warning(f"Found {len(invalid_indices)} records with null values in critical fields")
        for detail in invalid_details[:5]:  # Log first 5 details
            logger.debug(f"Invalid record at index {detail['index']}: null in {detail['null_fields']}")
        
        # Raise exception with details
        raise SchemaMismatchError(
            f"Schema validation failed: {len(invalid_indices)} records have null values "
            f"in required fields. Details: {invalid_details[:3]}"
        )
    
    logger.info(f"Validation passed: {valid_count}/{len(records)} records are valid")
    return valid_count


def validate_schema_structure(
    records: List[Any],
    required_fields: Set[str],
    record_type: Optional[Type] = None
) -> None:
    """
    Validate that records have the expected schema structure.
    
    Args:
        records: List of records to validate.
        required_fields: Set of field names that must exist in every record.
        record_type: Optional dataclass type for reference.
    
    Raises:
        SchemaMismatchError: If any record is missing required fields.
    """
    if not records:
        return
    
    first_record = records[0]
    existing_fields = set()
    
    if is_dataclass(first_record) and not isinstance(first_record, type):
        existing_fields = {f.name for f in fields(first_record)}
    elif isinstance(first_record, dict):
        existing_fields = set(first_record.keys())
    
    missing_fields = required_fields - existing_fields
    if missing_fields:
        raise SchemaMismatchError(
            f"Schema structure mismatch: missing required fields {missing_fields} "
            f"in records. Expected fields: {required_fields}, Found: {existing_fields}"
        )
    
    logger.debug("Schema structure validation passed")


def filter_null_records(
    records: List[Any],
    schema_fields: Optional[Set[str]] = None
) -> List[Any]:
    """
    Filter out records that have null values in critical fields.
    
    Args:
        records: List of records to filter.
        schema_fields: Optional set of field names to check for nulls.
                       If None, checks all fields.
    
    Returns:
        List[Any]: List of records with no null values in critical fields.
    """
    if not records:
        return []
    
    check_fields = schema_fields
    if check_fields is None:
        first_record = records[0]
        if is_dataclass(first_record) and not isinstance(first_record, type):
            check_fields = {f.name for f in fields(first_record)}
        elif isinstance(first_record, dict):
            check_fields = set(first_record.keys())
        else:
            return records  # Cannot determine fields, return as-is
    
    valid_records = []
    invalid_count = 0
    
    for record in records:
        if is_dataclass(record) and not isinstance(record, type):
            record_dict = {f.name: getattr(record, f.name) for f in fields(record)}
        elif isinstance(record, dict):
            record_dict = record
        else:
            valid_records.append(record)
            continue
        
        if all(record_dict.get(f) is not None for f in check_fields):
            valid_records.append(record)
        else:
            invalid_count += 1
    
    if invalid_count > 0:
        logger.warning(f"Filtered out {invalid_count} records with null values")
    
    return valid_records
