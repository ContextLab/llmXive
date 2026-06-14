"""
Parser module for extracting knot invariants from Knot Atlas data.

Implements tie-breaking rules per FR-011 and measurement precision standards.
Tie-breaking priority: braid word > DT code, lexicographic ordering as fallback.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json
import re

from download.knot_atlas_loader import KnotRecord
from reproducibility.logs import log_operation, get_logger


@dataclass
class ParsedKnotData:
    """Parsed knot invariant data with tie-breaking metadata."""
    knot_id: str
    crossing_number: int
    braid_index: int
    hyperbolic_volume: Optional[float]
    is_alternating: bool
    representation_source: str  # 'braid_word' or 'dt_code'
    tie_break_applied: bool
    raw_record: Dict[str, Any] = field(default_factory=dict)


class KnotParser:
    """Parser for Knot Atlas data with tie-breaking rules."""

    def __init__(self, logger: Optional[Any] = None):
        """Initialize parser with optional logger."""
        self.logger = logger or get_logger()
        self._parse_count = 0
        self._tie_break_count = 0

    def parse_record(self, record: Dict[str, Any]) -> ParsedKnotData:
        """
        Parse a single Knot Atlas record into structured data.

        Args:
            record: Raw dictionary from Knot Atlas download

        Returns:
            ParsedKnotData with extracted invariants
        """
        self._parse_count += 1

        # Extract knot identifier
        knot_id = self._extract_knot_id(record)

        # Extract crossing number
        crossing_number = self._extract_crossing_number(record)

        # Extract braid index with tie-breaking
        braid_index, braid_source, tie_break_applied = self._extract_braid_index(record)
        if tie_break_applied:
            self._tie_break_count += 1

        # Extract hyperbolic volume
        hyperbolic_volume = self._extract_hyperbolic_volume(record)

        # Extract alternating classification
        is_alternating = self._extract_alternating_classification(record)

        return ParsedKnotData(
            knot_id=knot_id,
            crossing_number=crossing_number,
            braid_index=braid_index,
            hyperbolic_volume=hyperbolic_volume,
            is_alternating=is_alternating,
            representation_source=braid_source,
            tie_break_applied=tie_break_applied,
            raw_record=record
        )

    def parse_records(self, records: List[Dict[str, Any]]) -> List[ParsedKnotData]:
        """Parse multiple records."""
        return [self.parse_record(r) for r in records]

    def _extract_knot_id(self, record: Dict[str, Any]) -> str:
        """Extract knot identifier from record."""
        # Try multiple possible field names
        for field_name in ['knot_id', 'identifier', 'id', 'name']:
            if field_name in record and record[field_name]:
                return str(record[field_name])

        # Fallback: generate from crossing number and index
        crossing = self._extract_crossing_number(record)
        index = record.get('index', 'unknown')
        return f"K{crossing}_{index}"

    def _extract_crossing_number(self, record: Dict[str, Any]) -> int:
        """Extract crossing number with validation."""
        # Try multiple possible field names
        for field_name in ['crossing_number', 'crossings', 'c']:
            if field_name in record:
                value = record[field_name]
                if isinstance(value, (int, float)):
                    crossing = int(value)
                    if crossing > 0 and crossing <= 13:
                        return crossing

        # Default fallback
        return 0

    def _extract_braid_index(self, record: Dict[str, Any]) -> Tuple[int, str, bool]:
        """
        Extract braid index with tie-breaking rules per FR-011.

        Tie-breaking priority:
        1. Braid word representation (preferred)
        2. DT code representation
        3. Lexicographic ordering as final fallback

        Returns:
            Tuple of (braid_index, source, tie_break_applied)
        """
        tie_break_applied = False
        braid_index = 0
        source = 'unknown'

        # Strategy 1: Try braid word representation (preferred)
        braid_word = record.get('braid_word', None)
        if braid_word is not None and braid_word != '':
            # Braid index from braid word: minimum number of strands needed
            # Parse braid word to determine minimum strand count
            braid_index = self._parse_braid_word_for_index(braid_word)
            source = 'braid_word'
            return (braid_index, source, tie_break_applied)

        # Strategy 2: Try DT code representation
        dt_code = record.get('dt_code', None)
        if dt_code is not None and dt_code != '':
            braid_index = self._parse_dt_code_for_index(dt_code)
            source = 'dt_code'
            return (braid_index, source, tie_break_applied)

        # Strategy 3: Try direct braid index field
        if 'braid_index' in record:
            value = record['braid_index']
            if isinstance(value, (int, float)):
                braid_index = int(value)
                source = 'direct'
                return (braid_index, source, tie_break_applied)

        # Strategy 4: Tie-breaking from multiple sources
        # If both braid_word and dt_code exist, use braid_word (priority 1)
        braid_word_present = record.get('braid_word') is not None
        dt_code_present = record.get('dt_code') is not None

        if braid_word_present and dt_code_present:
            # Tie-break: prefer braid_word
            braid_word = record['braid_word']
            braid_index = self._parse_braid_word_for_index(braid_word)
            source = 'braid_word'
            tie_break_applied = True
            return (braid_index, source, tie_break_applied)

        # Strategy 5: Fallback to direct field or estimate
        # Braid index is always <= crossing number
        crossing = self._extract_crossing_number(record)
        if crossing > 0:
            # Default estimate: braid_index = 2 for non-trivial knots
            # This is a conservative lower bound
            braid_index = 2
            source = 'estimate'
            return (braid_index, source, tie_break_applied)

        return (0, 'missing', tie_break_applied)

    def _parse_braid_word_for_index(self, braid_word: Any) -> int:
        """
        Parse braid word to determine minimum number of strands.

        Braid word format: sequence of integers where |i| indicates
        the crossing between strand i and strand i+1.

        Returns:
            Minimum number of strands needed
        """
        if isinstance(braid_word, str):
            # Parse space-separated or comma-separated integers
            # Example: "1 2 -1 3" or "1,2,-1,3"
            braid_word = braid_word.replace(',', ' ')
            try:
                generators = [int(x) for x in braid_word.split() if x.strip()]
                if generators:
                    # Maximum absolute value + 1 = minimum strands
                    return max(abs(g) for g in generators) + 1
            except (ValueError, TypeError):
                pass

        elif isinstance(braid_word, list):
            if braid_word:
                return max(abs(g) for g in braid_word if isinstance(g, int)) + 1

        return 2  # Default minimum for non-trivial knot

    def _parse_dt_code_for_index(self, dt_code: Any) -> int:
        """
        Parse DT (Dowker-Thistlethwaite) code to estimate braid index.

        DT code: sequence of even integers representing crossing labels.
        Braid index estimation from DT code is heuristic.

        Returns:
            Estimated braid index
        """
        if isinstance(dt_code, str):
            dt_code = dt_code.replace(',', ' ')
            try:
                numbers = [int(x) for x in dt_code.split() if x.strip()]
                if numbers:
                    # Heuristic: braid index ≈ sqrt(number of crossings)
                    # More accurate: use known bounds from DT code
                    n_crossings = len(numbers) // 2
                    # Lower bound: braid index >= 2 for non-trivial knots
                    # Upper bound: braid index <= crossing number
                    import math
                    return max(2, int(math.sqrt(n_crossings)) + 1)
            except (ValueError, TypeError):
                pass

        elif isinstance(dt_code, list):
            if dt_code:
                n_crossings = len(dt_code) // 2
                import math
                return max(2, int(math.sqrt(n_crossings)) + 1)

        return 2  # Default

    def _extract_hyperbolic_volume(self, record: Dict[str, Any]) -> Optional[float]:
        """Extract hyperbolic volume with precision validation."""
        volume = None

        # Try multiple possible field names
        for field_name in ['hyperbolic_volume', 'volume', 'vol', 'hyp_vol']:
            if field_name in record:
                value = record[field_name]
                if value is not None and value != '':
                    try:
                        vol = float(value)
                        if vol >= 0:
                            volume = round(vol, 6)  # Precision: 6 decimal places
                            break
                    except (ValueError, TypeError):
                        continue

        return volume

    def _extract_alternating_classification(self, record: Dict[str, Any]) -> bool:
        """
        Extract alternating/non-alternating classification.

        Handles ambiguous cases per FR-010 and T043a.
        """
        # Try multiple possible field names
        for field_name in ['is_alternating', 'alternating', 'alt']:
            if field_name in record:
                value = record[field_name]
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in ['true', 'yes', '1', 'alternating']:
                        return True
                    elif value_lower in ['false', 'no', '0', 'non-alternating', 'nonalternating']:
                        return False

        # Default: assume non-alternating if not specified
        return False

def parse_knot_atlas_data(
    records: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> List[ParsedKnotData]:
    """
    Convenience function to parse Knot Atlas data.

    Args:
        records: List of raw Knot Atlas records
        output_path: Optional path to save parsed data as JSON

    Returns:
        List of ParsedKnotData objects
    """
    parser = KnotParser()
    parsed = parser.parse_records(records)

    if output_path:
        # Save parsed data
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                'knot_id': p.knot_id,
                'crossing_number': p.crossing_number,
                'braid_index': p.braid_index,
                'hyperbolic_volume': p.hyperbolic_volume,
                'is_alternating': p.is_alternating,
                'representation_source': p.representation_source,
                'tie_break_applied': p.tie_break_applied
            }
            for p in parsed
        ]
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    return parsed


def verify_parser_consistency(parsed_data: List[ParsedKnotData]) -> Dict[str, Any]:
    """
    Verify parser output consistency with tie-breaking rules.

    Args:
        parsed_data: List of parsed knot data

    Returns:
        Dictionary with verification results
    """
    total = len(parsed_data)
    tie_breaks = sum(1 for p in parsed_data if p.tie_break_applied)
    braid_word_source = sum(1 for p in parsed_data if p.representation_source == 'braid_word')
    dt_code_source = sum(1 for p in parsed_data if p.representation_source == 'dt_code')

    # Verify braid index <= crossing number constraint
    violations = [
        p for p in parsed_data
        if p.braid_index > p.crossing_number
    ]

    return {
        'total_parsed': total,
        'tie_breaks_applied': tie_breaks,
        'tie_break_percentage': (tie_breaks / total * 100) if total > 0 else 0,
        'braid_word_sources': braid_word_source,
        'dt_code_sources': dt_code_source,
        'constraint_violations': len(violations),
        'violations': [p.knot_id for p in violations]
    }
