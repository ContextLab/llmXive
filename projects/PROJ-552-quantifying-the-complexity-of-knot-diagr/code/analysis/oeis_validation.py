"""
OEIS A002863 Validation Module

Validates crossing number counts against OEIS sequence A002863:
Number of prime knots with n crossings.

Per SC-001: Validation scope must be documented with concrete reference
to OEIS A002863 (https://oeis.org/A002863).
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from reproducibility.logs import log_operation, get_logger

# OEIS A002863 reference values for prime knots by crossing number (n <= 13)
# Source: https://oeis.org/A002863
OEIS_A002863_REFERENCE = {
    0: 1,   # unknot
    1: 0,   # no prime knots
    2: 0,   # no prime knots
    3: 1,   # trefoil
    4: 1,   # figure-eight
    5: 2,
    6: 3,
    7: 7,
    8: 21,
    9: 49,
    10: 165,
    11: 552,
    12: 2176,
    13: 9988,
}

@dataclass
class ValidationEntry:
    """Entry for OEIS validation comparison."""
    crossing_number: int
    expected_count: int
    actual_count: int
    match: bool
    deviation: int

@dataclass
class ValidationResult:
    """Complete validation result."""
    source: str
    total_crossing_numbers_validated: int
    matches: int
    mismatches: int
    entries: List[ValidationEntry]
    validation_passed: bool
    notes: str

class OeisValidator:
    """Validator for OEIS A002863 crossing number sequence."""

    def __init__(self, data_path: Path, logger=None):
        """
        Initialize validator.

        Args:
            data_path: Path to cleaned knots CSV file
            logger: ReproducibilityLogger instance (optional)
        """
        self.data_path = data_path
        self.logger = logger
        self.logger_instance = get_logger() if logger is None else logger

    def load_cleaned_knots(self) -> List[Dict[str, Any]]:
        """Load cleaned knot data from CSV."""
        knots = []
        with open(self.data_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                knots.append(row)
        return knots

    def count_knots_per_crossing_number(self, knots: List[Dict[str, Any]]) -> Dict[int, int]:
        """
        Count knots grouped by crossing number.

        Args:
            knots: List of knot records

        Returns:
            Dictionary mapping crossing number to count
        """
        counts = {}
        for knot in knots:
            cn = int(knot.get('crossing_number', 0))
            counts[cn] = counts.get(cn, 0) + 1
        return counts

    def validate_against_oeis(self, actual_counts: Dict[int, int]) -> ValidationResult:
        """
        Validate actual counts against OEIS A002863 reference.

        Args:
            actual_counts: Dictionary of crossing number -> actual count

        Returns:
            ValidationResult with comparison details
        """
        entries = []
        matches = 0
        mismatches = 0

        for cn in sorted(OEIS_A002863_REFERENCE.keys()):
            expected = OEIS_A002863_REFERENCE[cn]
            actual = actual_counts.get(cn, 0)
            match = (expected == actual)
            deviation = actual - expected

            if match:
                matches += 1
            else:
                mismatches += 1

            entries.append(ValidationEntry(
                crossing_number=cn,
                expected_count=expected,
                actual_count=actual,
                match=match,
                deviation=deviation
            ))

        # Validation passes if all counts match
        validation_passed = (mismatches == 0)

        notes = (
            f"OEIS A002863 validation complete. "
            f"Validated {len(entries)} crossing numbers. "
            f"Matches: {matches}, Mismatches: {mismatches}. "
            f"Reference: https://oeis.org/A002863"
        )

        return ValidationResult(
            source="OEIS A002863",
            total_crossing_numbers_validated=len(entries),
            matches=matches,
            mismatches=mismatches,
            entries=entries,
            validation_passed=validation_passed,
            notes=notes
        )

    def run_validation(self) -> ValidationResult:
        """
        Execute full validation pipeline.

        Returns:
            ValidationResult with all validation details
        """
        log_operation(
            operation="oeis_validation",
            input_file=str(self.data_path),
            output_file="validation_scope.md",
            parameters={"oeis_sequence": "A002863"},
            logger=self.logger_instance
        )

        knots = self.load_cleaned_knots()
        actual_counts = self.count_knots_per_crossing_number(knots)
        result = self.validate_against_oeis(actual_counts)

        log_operation(
            operation="oeis_validation_complete",
            input_file=str(self.data_path),
            output_file="validation_scope.md",
            parameters={
                "validation_passed": result.validation_passed,
                "matches": result.matches,
                "mismatches": result.mismatches
            },
            logger=self.logger_instance
        )

        return result

    def save_results(self, result: ValidationResult, output_path: Path):
        """
        Save validation results to JSON file.

        Args:
            result: ValidationResult instance
            output_path: Path to save results JSON
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'source': result.source,
                'total_crossing_numbers_validated': result.total_crossing_numbers_validated,
                'matches': result.matches,
                'mismatches': result.mismatches,
                'validation_passed': result.validation_passed,
                'notes': result.notes,
                'entries': [asdict(e) for e in result.entries]
            }, f, indent=2)

def load_cleaned_knots(data_path: Path) -> List[Dict[str, Any]]:
    """Convenience function to load cleaned knots."""
    knots = []
    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knots.append(row)
    return knots

def count_knots_per_crossing_number(knots: List[Dict[str, Any]]) -> Dict[int, int]:
    """Convenience function to count knots by crossing number."""
    counts = {}
    for knot in knots:
        cn = int(knot.get('crossing_number', 0))
        counts[cn] = counts.get(cn, 0) + 1
    return counts

def validate_oeis_a002863(data_path: Path, output_path: Path = None) -> ValidationResult:
    """
    Main validation function for OEIS A002863.

    Args:
        data_path: Path to cleaned knots CSV
        output_path: Optional path to save JSON results

    Returns:
        ValidationResult instance
    """
    validator = OeisValidator(data_path)
    result = validator.run_validation()

    if output_path:
        validator.save_results(result, output_path)

    return result

def main():
    """Main entry point for OEIS validation."""
    import sys

    # Default paths
    data_path = Path('data/processed/knots_cleaned.csv')
    output_path = Path('data/processed/oeis_validation_results.json')

    # Allow command-line override
    if len(sys.argv) > 1:
        data_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)

    print(f"Validating OEIS A002863 for: {data_path}")
    result = validate_oeis_a002863(data_path, output_path)

    print(f"\nValidation Results:")
    print(f"  Source: {result.source}")
    print(f"  Total crossing numbers validated: {result.total_crossing_numbers_validated}")
    print(f"  Matches: {result.matches}")
    print(f"  Mismatches: {result.mismatches}")
    print(f"  Validation passed: {result.validation_passed}")
    print(f"\n  Notes: {result.notes}")

    if output_path:
        print(f"\nResults saved to: {output_path}")

    # Exit with error code if validation failed
    sys.exit(0 if result.validation_passed else 1)

if __name__ == '__main__':
    main()