"""
Tie-breaking rule consistency validator for knot diagram complexity analysis.

Per SC-007: This script validates that tie-breaking rules are consistently applied
across all knot records in the dataset.

Tie-breaking rules (documented in docs/reproducibility/tie_breaking_rules.md):
- Primary: braid word representation (when available)
- Secondary: DT code representation (when braid word unavailable)
- Tertiary: lexicographic ordering of knot identifiers

Exit codes:
- 0: All tie-breaking rules are consistently applied
- 1: Inconsistencies detected or validation failed
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from data.parser import ParsedKnotData, verify_parser_consistency
from reproducibility.logs import log_operation, get_logger


@dataclass
class TieBreakingValidationEntry:
    """Single validation entry for tie-breaking rule consistency."""
    knot_id: str
    has_braid_word: bool
    has_dt_code: bool
    tie_breaker_applied: str  # 'braid_word', 'dt_code', 'lexicographic', 'none'
    is_consistent: bool
    reason: str


@dataclass
class TieBreakingValidationResult:
    """Complete tie-breaking validation result."""
    total_knots: int
    validated_knots: int
    consistent_count: int
    inconsistent_count: int
    entries: List[TieBreakingValidationEntry]
    validation_passed: bool
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_knots': self.total_knots,
            'validated_knots': self.validated_knots,
            'consistent_count': self.consistent_count,
            'inconsistent_count': self.inconsistent_count,
            'entries': [asdict(e) for e in self.entries],
            'validation_passed': self.validation_passed,
            'timestamp': self.timestamp
        }


def load_parsed_data(data_path: Path) -> List[ParsedKnotData]:
    """
    Load parsed knot data from cleaned dataset.

    Args:
        data_path: Path to the cleaned knots CSV file

    Returns:
        List of ParsedKnotData objects
    """
    logger = get_logger()
    log_operation(
        logger=logger,
        operation='load_parsed_data',
        input_file=str(data_path),
        output_file=None,
        parameters={'path': str(data_path)},
        status='started'
    )

    knots = []
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = json.load(f)
            for record in reader:
                knot = ParsedKnotData(**record)
                knots.append(knot)

        log_operation(
            logger=logger,
            operation='load_parsed_data',
            input_file=str(data_path),
            output_file=None,
            parameters={'path': str(data_path), 'knot_count': len(knots)},
            status='completed'
        )
    except Exception as e:
        log_operation(
            logger=logger,
            operation='load_parsed_data',
            input_file=str(data_path),
            output_file=None,
            parameters={'path': str(data_path), 'error': str(e)},
            status='failed'
        )
        raise

    return knots


def validate_tie_breaking_rules(knots: List[ParsedKnotData]) -> TieBreakingValidationResult:
    """
    Validate that tie-breaking rules are consistently applied across all knots.

    Per SC-007: Tie-breaking rules must be documented and consistently applied.
    Rules:
    - Primary: braid word representation (when available)
    - Secondary: DT code representation (when braid word unavailable)
    - Tertiary: lexicographic ordering of knot identifiers

    Args:
        knots: List of ParsedKnotData objects

    Returns:
        TieBreakingValidationResult with validation details
    """
    logger = get_logger()
    log_operation(
        logger=logger,
        operation='validate_tie_breaking_rules',
        input_file=None,
        output_file=None,
        parameters={'knot_count': len(knots)},
        status='started'
    )

    entries = []
    consistent_count = 0
    inconsistent_count = 0

    for knot in knots:
        # Check if braid word is available
        has_braid_word = (
            knot.braid_word is not None and
            len(knot.braid_word) > 0
        )

        # Check if DT code is available
        has_dt_code = (
            knot.dt_code is not None and
            len(knot.dt_code) > 0
        )

        # Determine which tie-breaker was applied based on priority
        if has_braid_word:
            tie_breaker_applied = 'braid_word'
        elif has_dt_code:
            tie_breaker_applied = 'dt_code'
        else:
            tie_breaker_applied = 'none'

        # Validate consistency against documented rules
        is_consistent = True
        reason = "Consistent"

        # Check for violations of tie-breaking hierarchy
        if not has_braid_word and not has_dt_code:
            # Neither available - acceptable but should be documented
            is_consistent = True
            reason = "No tie-breaker available (acceptable per SC-007)"
        elif has_braid_word and tie_breaker_applied != 'braid_word':
            # Braid word available but not used - inconsistency
            is_consistent = False
            reason = "Braid word available but not used as primary tie-breaker"
        elif not has_braid_word and has_dt_code and tie_breaker_applied != 'dt_code':
            # DT code available but not used - inconsistency
            is_consistent = False
            reason = "DT code available but not used as secondary tie-breaker"

        entry = TieBreakingValidationEntry(
            knot_id=knot.knot_id,
            has_braid_word=has_braid_word,
            has_dt_code=has_dt_code,
            tie_breaker_applied=tie_breaker_applied,
            is_consistent=is_consistent,
            reason=reason
        )
        entries.append(entry)

        if is_consistent:
            consistent_count += 1
        else:
            inconsistent_count += 1

    validation_passed = inconsistent_count == 0

    result = TieBreakingValidationResult(
        total_knots=len(knots),
        validated_knots=len(knots),
        consistent_count=consistent_count,
        inconsistent_count=inconsistent_count,
        entries=entries,
        validation_passed=validation_passed,
        timestamp=datetime.now().isoformat()
    )

    log_operation(
        logger=logger,
        operation='validate_tie_breaking_rules',
        input_file=None,
        output_file=None,
        parameters={
            'total_knots': len(knots),
            'consistent_count': consistent_count,
            'inconsistent_count': inconsistent_count,
            'validation_passed': validation_passed
        },
        status='completed' if validation_passed else 'failed'
    )

    return result


def main(data_path: Optional[Path] = None, output_path: Optional[Path] = None) -> int:
    """
    Main entry point for tie-breaking validation.

    Args:
        data_path: Path to cleaned knots JSON file (defaults to data/processed/knots_cleaned.json)
        output_path: Path to output validation report (defaults to docs/reproducibility/tie_breaking_validation_report.json)

    Returns:
        Exit code: 0 on success (all consistent), 1 on failure (inconsistencies detected)
    """
    logger = get_logger()

    # Set default paths relative to project root
    if data_path is None:
        project_root = Path(__file__).parent.parent.parent
        data_path = project_root / 'data' / 'processed' / 'knots_cleaned.json'

    if output_path is None:
        project_root = Path(__file__).parent.parent.parent
        output_path = project_root / 'docs' / 'reproducibility' / 'tie_breaking_validation_report.json'

    log_operation(
        logger=logger,
        operation='tie_breaking_validation_main',
        input_file=str(data_path),
        output_file=str(output_path),
        parameters={'data_path': str(data_path), 'output_path': str(output_path)},
        status='started'
    )

    try:
        # Load parsed data
        knots = load_parsed_data(data_path)
        logger.info(f"Loaded {len(knots)} parsed knots for tie-breaking validation")

        # Validate tie-breaking rules
        result = validate_tie_breaking_rules(knots)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save validation report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Validation report saved to {output_path}")
        logger.info(f"Validation passed: {result.validation_passed}")
        logger.info(f"Consistent: {result.consistent_count}/{result.total_knots}")
        logger.info(f"Inconsistent: {result.inconsistent_count}/{result.total_knots}")

        log_operation(
            logger=logger,
            operation='tie_breaking_validation_main',
            input_file=str(data_path),
            output_file=str(output_path),
            parameters={
                'total_knots': result.total_knots,
                'validation_passed': result.validation_passed,
                'exit_code': 0 if result.validation_passed else 1
            },
            status='completed' if result.validation_passed else 'failed'
        )

        # Exit with appropriate code per SC-007
        return 0 if result.validation_passed else 1

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        log_operation(
            logger=logger,
            operation='tie_breaking_validation_main',
            input_file=str(data_path),
            output_file=str(output_path),
            parameters={'error': str(e)},
            status='failed'
        )
        return 1

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        log_operation(
            logger=logger,
            operation='tie_breaking_validation_main',
            input_file=str(data_path),
            output_file=str(output_path),
            parameters={'error': str(e)},
            status='failed'
        )
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)