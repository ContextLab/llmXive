"""
Plausibility validation logic for compliance logs (FR-010).

This module validates that daily compliance log entries contain
plausible values within physically possible bounds.

Rules:
- Minutes spent on any activity must be >= 0 and <= 1440 (24 hours).
- Percentage values (if present) must be between 0 and 100.
- Timestamps must be valid and not in the future relative to processing time.
- Required fields (participant_id, date, activity_type, duration_minutes) must be present.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlausibilityError:
    """Represents a single plausibility validation error."""
    participant_id: str
    date: str
    field: str
    value: Any
    message: str
    error_type: str  # 'missing', 'out_of_bounds', 'invalid_type', 'future_date'


@dataclass
class PlausibilityResult:
    """Result of plausibility validation for a batch of logs."""
    valid_count: int
    invalid_count: int
    errors: List[PlausibilityError]
    summary: Dict[str, int]

def validate_plausibility(
    logs: List[Dict[str, Any]],
    max_minutes: int = 1440,
    check_future_dates: bool = True
) -> PlausibilityResult:
    """
    Validate a list of compliance log entries for plausibility.

    Args:
        logs: List of dictionaries containing compliance log data.
        max_minutes: Maximum allowed minutes in a day (default 1440).
        check_future_dates: Whether to flag timestamps in the future.

    Returns:
        PlausibilityResult with counts and list of errors.
    """
    errors: List[PlausibilityError] = []
    valid_count = 0
    invalid_ids: set = set()

    required_fields = ['participant_id', 'date', 'activity_type', 'duration_minutes']

    for idx, log in enumerate(logs):
        log_id = f"log_{idx}"
        participant_id = log.get('participant_id', 'UNKNOWN')
        date_val = log.get('date', 'UNKNOWN')

        is_valid = True

        # Check required fields
        for field in required_fields:
            if field not in log or log[field] is None:
                errors.append(PlausibilityError(
                    participant_id=participant_id,
                    date=str(date_val),
                    field=field,
                    value=None,
                    message=f"Required field '{field}' is missing or null",
                    error_type='missing'
                ))
                is_valid = False
                invalid_ids.add(participant_id)

        if not is_valid:
            continue

        # Validate duration_minutes
        duration = log.get('duration_minutes')
        if duration is not None:
            try:
                duration_float = float(duration)
                if duration_float < 0:
                    errors.append(PlausibilityError(
                        participant_id=participant_id,
                        date=str(date_val),
                        field='duration_minutes',
                        value=duration,
                        message=f"Duration cannot be negative: {duration}",
                        error_type='out_of_bounds'
                    ))
                    is_valid = False
                    invalid_ids.add(participant_id)
                elif duration_float > max_minutes:
                    errors.append(PlausibilityError(
                        participant_id=participant_id,
                        date=str(date_val),
                        field='duration_minutes',
                        value=duration,
                        message=f"Duration exceeds maximum possible minutes in a day ({max_minutes}): {duration}",
                        error_type='out_of_bounds'
                    ))
                    is_valid = False
                    invalid_ids.add(participant_id)
            except (ValueError, TypeError):
                errors.append(PlausibilityError(
                    participant_id=participant_id,
                    date=str(date_val),
                    field='duration_minutes',
                    value=duration,
                    message=f"Invalid duration format: {duration}",
                    error_type='invalid_type'
                ))
                is_valid = False
                invalid_ids.add(participant_id)

        # Validate percentage fields if present
        for key, value in log.items():
            if isinstance(value, (int, float)) and key.endswith('_percent'):
                if value < 0 or value > 100:
                    errors.append(PlausibilityError(
                        participant_id=participant_id,
                        date=str(date_val),
                        field=key,
                        value=value,
                        message=f"Percentage value {value} is out of range [0, 100]",
                        error_type='out_of_bounds'
                    ))
                    is_valid = False
                    invalid_ids.add(participant_id)

        # Validate date/timestamp if present and check for future
        if check_future_dates and 'timestamp' in log:
            try:
                ts = log['timestamp']
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                elif isinstance(ts, datetime):
                    dt = ts
                else:
                    dt = datetime.fromtimestamp(ts)

                if dt > datetime.now(dt.tzinfo if dt.tzinfo else None):
                    errors.append(PlausibilityError(
                        participant_id=participant_id,
                        date=str(date_val),
                        field='timestamp',
                        value=ts,
                        message=f"Timestamp is in the future: {ts}",
                        error_type='future_date'
                    ))
                    is_valid = False
                    invalid_ids.add(participant_id)
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Could not parse timestamp for {participant_id} on {date_val}: {e}")

        if is_valid:
            valid_count += 1
        else:
            invalid_ids.add(participant_id)

    # Calculate summary
    error_summary = {}
    for err in errors:
        key = f"{err.error_type}:{err.field}"
        error_summary[key] = error_summary.get(key, 0) + 1

    return PlausibilityResult(
        valid_count=valid_count,
        invalid_count=len(invalid_ids),
        errors=errors,
        summary=error_summary
    )


def validate_plausibility_file(
    input_path: str,
    output_path: Optional[str] = None
) -> PlausibilityResult:
    """
    Load compliance logs from a JSON file and validate plausibility.

    Args:
        input_path: Path to the JSON file containing compliance logs.
        output_path: Optional path to write a JSON report of errors.

    Returns:
        PlausibilityResult with validation outcomes.
    """
    import json
    from pathlib import Path

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    # Handle if the JSON is a single object or a list
    if isinstance(logs, dict):
        logs = [logs]

    result = validate_plausibility(logs)

    if output_path:
        report = {
            "valid_count": result.valid_count,
            "invalid_count": result.invalid_count,
            "total_checked": result.valid_count + result.invalid_count,
            "summary": result.summary,
            "errors": [
                {
                    "participant_id": e.participant_id,
                    "date": e.date,
                    "field": e.field,
                    "value": str(e.value),
                    "message": e.message,
                    "error_type": e.error_type
                }
                for e in result.errors
            ]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Plausibility validation report written to {output_path}")

    return result


def main():
    """CLI entry point for plausibility validation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Validate compliance log entries for plausibility (FR-010)."
    )
    parser.add_argument(
        "input_file",
        help="Path to JSON file containing compliance logs."
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to write JSON validation report (optional)."
    )
    parser.add_argument(
        "--max-minutes",
        type=int,
        default=1440,
        help="Maximum allowed minutes in a day (default: 1440)."
    )
    parser.add_argument(
        "--no-future-check",
        action="store_true",
        help="Disable future date checking."
    )

    args = parser.parse_args()

    try:
        result = validate_plausibility_file(
            args.input_file,
            output_path=args.output
        )

        print(f"Plausibility Validation Results:")
        print(f"  Valid entries:   {result.valid_count}")
        print(f"  Invalid entries: {result.invalid_count}")
        print(f"  Total errors:    {len(result.errors)}")

        if result.summary:
            print(f"\nError Summary:")
            for key, count in sorted(result.summary.items()):
                print(f"  {key}: {count}")

        if result.errors:
            print(f"\nFirst 5 errors:")
            for err in result.errors[:5]:
                print(f"  [{err.error_type}] {err.participant_id} ({err.date}): {err.message}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors.")

        sys.exit(0 if result.invalid_count == 0 else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()