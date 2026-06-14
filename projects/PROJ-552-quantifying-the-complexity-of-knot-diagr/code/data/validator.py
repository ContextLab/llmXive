"""
Data quality validation module for knot diagram complexity analysis.

Implements data cleaning to flag nulls and format failures per FR-002.
Provides validation for missing invariants and data quality issues.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from pathlib import Path
import json
from datetime import datetime

from reproducibility.logs import log_operation, ReproducibilityLogger


@dataclass
class DataQualityFlag:
    """Represents a single data quality issue flag."""
    record_id: str
    field_name: str
    flag_type: str  # 'null', 'format_failure', 'duplicate', 'range_violation', 'classification_invalid'
    message: str
    severity: str = 'warning'  # 'warning' or 'error'


@dataclass
class DataQualityFlags:
    """Container for all data quality flags on a dataset."""
    flags: List[DataQualityFlag] = field(default_factory=list)
    null_flags: List[DataQualityFlag] = field(default_factory=list)
    format_flags: List[DataQualityFlag] = field(default_factory=list)
    duplicate_flags: List[DataQualityFlag] = field(default_factory=list)
    range_flags: List[DataQualityFlag] = field(default_factory=list)
    classification_flags: List[DataQualityFlag] = field(default_factory=list)

    def add_flag(self, flag: DataQualityFlag) -> None:
        """Add a flag to the appropriate category."""
        self.flags.append(flag)
        if flag.flag_type == 'null':
            self.null_flags.append(flag)
        elif flag.flag_type == 'format_failure':
            self.format_flags.append(flag)
        elif flag.flag_type == 'duplicate':
            self.duplicate_flags.append(flag)
        elif flag.flag_type == 'range_violation':
            self.range_flags.append(flag)
        elif flag.flag_type == 'classification_invalid':
            self.classification_flags.append(flag)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all flags."""
        return {
            'total_flags': len(self.flags),
            'null_flags': len(self.null_flags),
            'format_flags': len(self.format_flags),
            'duplicate_flags': len(self.duplicate_flags),
            'range_flags': len(self.range_flags),
            'classification_flags': len(self.classification_flags),
        }


@dataclass
class MissingInvariantFlag:
    """Represents a missing invariant flag per FR-009."""
    record_id: str
    invariant_name: str
    message: str


@dataclass
class MissingInvariantFlags:
    """Container for all missing invariant flags."""
    flags: List[MissingInvariantFlag] = field(default_factory=list)

    def add_flag(self, flag: MissingInvariantFlag) -> None:
        """Add a missing invariant flag."""
        self.flags.append(flag)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of missing invariant flags."""
        return {
            'total_missing': len(self.flags),
            'by_invariant': self._group_by_invariant(),
        }

    def _group_by_invariant(self) -> Dict[str, int]:
        """Group missing flags by invariant name."""
        counts: Dict[str, int] = {}
        for flag in self.flags:
            counts[flag.invariant_name] = counts.get(flag.invariant_name, 0) + 1
        return counts


def check_null_values(
    records: List[Dict[str, Any]],
    required_fields: List[str],
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Check for null/missing values in required fields.

    Per FR-002: null percentage must be ≤5% for critical fields.

    Args:
        records: List of knot record dictionaries.
        required_fields: List of field names that must not be null.
        logger: Optional reproducibility logger for operation logging.

    Returns:
        DataQualityFlags containing all null-related flags.
    """
    flags = DataQualityFlags()
    total_cells = len(records) * len(required_fields)
    null_count = 0

    for record in records:
        record_id = record.get('id', record.get('knot_id', 'unknown'))
        for field_name in required_fields:
            value = record.get(field_name)
            if value is None or value == '' or value == '':
                null_count += 1
                flag = DataQualityFlag(
                    record_id=record_id,
                    field_name=field_name,
                    flag_type='null',
                    message=f"Field '{field_name}' is null or empty",
                    severity='error' if field_name in ['crossing_number', 'braid_index'] else 'warning'
                )
                flags.add_flag(flag)

    if logger:
        log_operation(
            logger=logger,
            operation='check_null_values',
            input_file='records',
            output_file=None,
            parameters={'required_fields': required_fields, 'null_count': null_count, 'total_cells': total_cells},
            status='completed'
        )

    return flags


def check_format_validity(
    records: List[Dict[str, Any]],
    format_rules: Dict[str, str],
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Check format validity of fields against specified rules.

    Per FR-002: format pass rate must be ≥99%.

    Format rules are specified as:
    - 'crossing_number': 'integer'
    - 'braid_index': 'integer'
    - 'hyperbolic_volume': 'float'
    - 'alternating': 'boolean'
    - 'braid_word': 'comma_separated_integers'
    - 'dt_code': 'comma_separated_integers'

    Args:
        records: List of knot record dictionaries.
        format_rules: Dict mapping field names to expected formats.
        logger: Optional reproducibility logger.

    Returns:
        DataQualityFlags containing all format-related flags.
    """
    flags = DataQualityFlags()
    total_fields = len(records) * len(format_rules)
    format_failures = 0

    for record in records:
        record_id = record.get('id', record.get('knot_id', 'unknown'))
        for field_name, expected_format in format_rules.items():
            if field_name not in record:
                continue

            value = record[field_name]
            is_valid = _validate_format(value, expected_format)

            if not is_valid:
                format_failures += 1
                flag = DataQualityFlag(
                    record_id=record_id,
                    field_name=field_name,
                    flag_type='format_failure',
                    message=f"Field '{field_name}' has invalid format (expected: {expected_format})",
                    severity='error'
                )
                flags.add_flag(flag)

    if logger:
        log_operation(
            logger=logger,
            operation='check_format_validity',
            input_file='records',
            output_file=None,
            parameters={'format_rules': format_rules, 'format_failures': format_failures, 'total_fields': total_fields},
            status='completed'
        )

    return flags


def check_duplicate_records(
    records: List[Dict[str, Any]],
    id_field: str = 'id',
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Check for duplicate records in the dataset.

    Per FR-002: duplicate records must be 0.

    Args:
        records: List of knot record dictionaries.
        id_field: Field name to use as unique identifier.
        logger: Optional reproducibility logger.

    Returns:
        DataQualityFlags containing all duplicate-related flags.
    """
    flags = DataQualityFlags()
    seen_ids: Set[str] = set()
    duplicate_ids: Set[str] = set()

    for record in records:
        record_id = record.get(id_field, 'unknown')
        if record_id in seen_ids:
            duplicate_ids.add(record_id)
        else:
            seen_ids.add(record_id)

    for dup_id in duplicate_ids:
        flag = DataQualityFlag(
            record_id=dup_id,
            field_name=id_field,
            flag_type='duplicate',
            message=f"Record ID '{dup_id}' appears multiple times in dataset",
            severity='error'
        )
        flags.add_flag(flag)

    if logger:
        log_operation(
            logger=logger,
            operation='check_duplicate_records',
            input_file='records',
            output_file=None,
            parameters={'id_field': id_field, 'duplicate_count': len(duplicate_ids)},
            status='completed'
        )

    return flags


def check_value_ranges(
    records: List[Dict[str, Any]],
    range_rules: Dict[str, Tuple[Optional[float], Optional[float]]],
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Check that numeric values fall within expected ranges.

    Args:
        records: List of knot record dictionaries.
        range_rules: Dict mapping field names to (min, max) tuples.
                    None means no bound on that side.
        logger: Optional reproducibility logger.

    Returns:
        DataQualityFlags containing all range-related flags.
    """
    flags = DataQualityFlags()

    for record in records:
        record_id = record.get('id', record.get('knot_id', 'unknown'))
        for field_name, (min_val, max_val) in range_rules.items():
            if field_name not in record:
                continue

            value = record[field_name]
            if not isinstance(value, (int, float)):
                continue

            if min_val is not None and value < min_val:
                flag = DataQualityFlag(
                    record_id=record_id,
                    field_name=field_name,
                    flag_type='range_violation',
                    message=f"Field '{field_name}' value {value} is below minimum {min_val}",
                    severity='warning'
                )
                flags.add_flag(flag)

            if max_val is not None and value > max_val:
                flag = DataQualityFlag(
                    record_id=record_id,
                    field_name=field_name,
                    flag_type='range_violation',
                    message=f"Field '{field_name}' value {value} is above maximum {max_val}",
                    severity='warning'
                )
                flags.add_flag(flag)

    if logger:
        log_operation(
            logger=logger,
            operation='check_value_ranges',
            input_file='records',
            output_file=None,
            parameters={'range_rules': range_rules},
            status='completed'
        )

    return flags


def check_classification_validity(
    records: List[Dict[str, Any]],
    valid_classifications: List[str],
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Check that classification fields contain only valid values.

    Per FR-010: ambiguous alternating/non-alternating classification should be excluded or marked as 'unclassifiable'.

    Args:
        records: List of knot record dictionaries.
        valid_classifications: List of valid classification values.
        logger: Optional reproducibility logger.

    Returns:
        DataQualityFlags containing all classification-related flags.
    """
    flags = DataQualityFlags()

    for record in records:
        record_id = record.get('id', record.get('knot_id', 'unknown'))
        alt_field = record.get('alternating')

        if alt_field is not None and alt_field not in valid_classifications:
            flag = DataQualityFlag(
                record_id=record_id,
                field_name='alternating',
                flag_type='classification_invalid',
                message=f"Field 'alternating' has invalid value '{alt_field}' (valid: {valid_classifications})",
                severity='warning'
            )
            flags.add_flag(flag)

    if logger:
        log_operation(
            logger=logger,
            operation='check_classification_validity',
            input_file='records',
            output_file=None,
            parameters={'valid_classifications': valid_classifications},
            status='completed'
        )

    return flags


def check_data_quality_issues(
    records: List[Dict[str, Any]],
    required_fields: List[str],
    format_rules: Dict[str, str],
    range_rules: Dict[str, Tuple[Optional[float], Optional[float]]],
    valid_classifications: List[str],
    logger: Optional[ReproducibilityLogger] = None
) -> DataQualityFlags:
    """
    Run all data quality checks on the dataset.

    Per FR-002:
    - null percentage ≤5%
    - format pass rate ≥99%
    - duplicate records = 0

    Args:
        records: List of knot record dictionaries.
        required_fields: Fields that must not be null.
        format_rules: Format validation rules.
        range_rules: Value range validation rules.
        valid_classifications: Valid classification values.
        logger: Optional reproducibility logger.

    Returns:
        Combined DataQualityFlags from all checks.
    """
    combined_flags = DataQualityFlags()

    # Run all checks
    null_flags = check_null_values(records, required_fields, logger)
    format_flags = check_format_validity(records, format_rules, logger)
    duplicate_flags = check_duplicate_records(records, logger=logger)
    range_flags = check_value_ranges(records, range_rules, logger)
    classification_flags = check_classification_validity(records, valid_classifications, logger)

    # Combine all flags
    for flag in null_flags.flags:
        combined_flags.add_flag(flag)
    for flag in format_flags.flags:
        combined_flags.add_flag(flag)
    for flag in duplicate_flags.flags:
        combined_flags.add_flag(flag)
    for flag in range_flags.flags:
        combined_flags.add_flag(flag)
    for flag in classification_flags.flags:
        combined_flags.add_flag(flag)

    return combined_flags


def validate_dataset_data_quality(
    records: List[Dict[str, Any]],
    required_fields: List[str],
    format_rules: Dict[str, str],
    range_rules: Dict[str, Tuple[Optional[float], Optional[float]]],
    valid_classifications: List[str],
    thresholds: Dict[str, float],
    logger: Optional[ReproducibilityLogger] = None
) -> Tuple[bool, DataQualityFlags, Dict[str, Any]]:
    """
    Validate dataset data quality against thresholds.

    Per FR-002 verification criteria:
    - null percentage ≤5%
    - format pass rate ≥99%
    - duplicate records = 0

    Args:
        records: List of knot record dictionaries.
        required_fields: Fields that must not be null.
        format_rules: Format validation rules.
        range_rules: Value range validation rules.
        valid_classifications: Valid classification values.
        thresholds: Dict with keys 'max_null_pct', 'min_format_pass_rate', 'max_duplicates'.
        logger: Optional reproducibility logger.

    Returns:
        Tuple of (is_valid, flags, summary_stats).
    """
    flags = check_data_quality_issues(
        records, required_fields, format_rules, range_rules, valid_classifications, logger
    )

    # Calculate metrics
    total_records = len(records)
    total_cells = total_records * len(required_fields)
    null_pct = (len(flags.null_flags) / total_cells * 100) if total_cells > 0 else 0.0

    total_format_fields = total_records * len(format_rules)
    format_pass_rate = ((total_format_fields - len(flags.format_flags)) / total_format_fields * 100) if total_format_fields > 0 else 100.0

    duplicate_count = len(flags.duplicate_flags)

    # Check thresholds
    is_valid = (
        null_pct <= thresholds.get('max_null_pct', 5.0) and
        format_pass_rate >= thresholds.get('min_format_pass_rate', 99.0) and
        duplicate_count <= thresholds.get('max_duplicates', 0)
    )

    summary_stats = {
        'total_records': total_records,
        'null_percentage': round(null_pct, 4),
        'format_pass_rate': round(format_pass_rate, 4),
        'duplicate_count': duplicate_count,
        'thresholds': thresholds,
        'passes_thresholds': is_valid,
    }

    return is_valid, flags, summary_stats


def write_data_quality_report(
    flags: DataQualityFlags,
    summary_stats: Dict[str, Any],
    output_path: Path,
    logger: Optional[ReproducibilityLogger] = None
) -> None:
    """
    Write data quality report to file.

    Args:
        flags: DataQualityFlags containing all issues.
        summary_stats: Summary statistics from validation.
        output_path: Path to write report.
        logger: Optional reproducibility logger.
    """
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'summary': summary_stats,
        'flag_counts': flags.get_summary(),
        'null_flags': [
            {
                'record_id': f.record_id,
                'field_name': f.field_name,
                'message': f.message,
                'severity': f.severity,
            }
            for f in flags.null_flags
        ],
        'format_flags': [
            {
                'record_id': f.record_id,
                'field_name': f.field_name,
                'message': f.message,
                'severity': f.severity,
            }
            for f in flags.format_flags
        ],
        'duplicate_flags': [
            {
                'record_id': f.record_id,
                'field_name': f.field_name,
                'message': f.message,
                'severity': f.severity,
            }
            for f in flags.duplicate_flags
        ],
        'range_flags': [
            {
                'record_id': f.record_id,
                'field_name': f.field_name,
                'message': f.message,
                'severity': f.severity,
            }
            for f in flags.range_flags
        ],
        'classification_flags': [
            {
                'record_id': f.record_id,
                'field_name': f.field_name,
                'message': f.message,
                'severity': f.severity,
            }
            for f in flags.classification_flags
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    if logger:
        log_operation(
            logger=logger,
            operation='write_data_quality_report',
            input_file=None,
            output_file=str(output_path),
            parameters={'flag_count': len(flags.flags)},
            status='completed'
        )


def get_data_quality_summary(flags: DataQualityFlags) -> Dict[str, Any]:
    """
    Get a human-readable summary of data quality issues.

    Args:
        flags: DataQualityFlags to summarize.

    Returns:
        Dict with summary statistics.
    """
    summary = flags.get_summary()
    summary['total_records_affected'] = len(set(f.record_id for f in flags.flags))
    summary['error_count'] = len([f for f in flags.flags if f.severity == 'error'])
    summary['warning_count'] = len([f for f in flags.flags if f.severity == 'warning'])
    return summary


def _validate_format(value: Any, expected_format: str) -> bool:
    """
    Internal helper to validate a value against an expected format.

    Args:
        value: Value to validate.
        expected_format: Expected format string.

    Returns:
        True if value matches expected format.
    """
    if value is None:
        return True  # Null handling is done separately

    if expected_format == 'integer':
        return isinstance(value, int) or (isinstance(value, str) and value.lstrip('-').isdigit())

    elif expected_format == 'float':
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False

    elif expected_format == 'boolean':
        return isinstance(value, bool) or value in ['true', 'false', 'True', 'False', '1', '0']

    elif expected_format == 'comma_separated_integers':
        if not isinstance(value, str):
            return False
        parts = value.split(',')
        return all(p.lstrip('-').isdigit() for p in parts if p.strip())

    elif expected_format == 'string':
        return isinstance(value, str)

    else:
        # Unknown format, assume valid
        return True
