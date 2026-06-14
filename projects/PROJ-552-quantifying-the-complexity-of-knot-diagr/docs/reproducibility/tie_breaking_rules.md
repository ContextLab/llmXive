# Tie-Breaking Rules for Knot Invariant Extraction

## Overview

This document specifies the tie-breaking rules used when extracting knot invariants
from Knot Atlas data, per FR-011 and Constitution Principle requirements.

When multiple representations of the same invariant are available, the following
priority order is applied:

## Priority Order

### 1. Braid Word Representation (Highest Priority)

When a braid word is available, it is the preferred source for braid index
extraction because:

- Braid words provide explicit strand information
- The minimum number of strands is directly computable
- Braid word representation is mathematically precise

**Extraction Method**: Parse the braid word to determine the minimum number
of strands required. The braid index is the maximum absolute value of any
generator index plus one.

Example:
- Braid word: "1 2 -1 3 2"
- Maximum generator index: 3
- Braid index: 3 + 1 = 4 strands

### 2. DT Code Representation (Second Priority)

When DT (Dowker-Thistlethwaite) code is available but braid word is not,
use DT code with the following estimation:

**Extraction Method**: Estimate braid index from the number of crossings
in the DT code using the heuristic:

```
braid_index ≈ max(2, floor(sqrt(n_crossings)) + 1)
```

where `n_crossings` is the number of crossings (half the length of the DT code).

Example:
- DT code: "4 6 8 2 4 6 8 2" (8 numbers = 4 crossings)
- n_crossings = 4
- braid_index ≈ max(2, floor(sqrt(4)) + 1) = max(2, 3) = 3

### 3. Direct Field (Third Priority)

When a direct `braid_index` field is present in the source data, use it
if no braid word or DT code is available.

### 4. Estimation (Lowest Priority)

When no representation is available, estimate braid index as:
- 2 for non-trivial knots (crossing number > 1)
- 1 for the unknot (crossing number = 0)

## Tie-Breaking Scenarios

### Scenario 1: Both Braid Word and DT Code Present

**Rule**: Prefer braid word representation.

**Rationale**: Braid word provides explicit strand information, while DT
code requires estimation. The braid word is more precise.

**Flagging**: Set `tie_break_applied = True` and `representation_source = 'braid_word'`

### Scenario 2: Multiple Braid Word Representations

**Rule**: Prefer the representation with minimum number of strands.

**Rationale**: The braid index is defined as the minimum number of strands
needed to represent the knot.

**Flagging**: Set `tie_break_applied = True`

### Scenario 3: Conflicting Braid Index Values

**Rule**: When direct field and braid word disagree, prefer braid word.

**Rationale**: Braid word is derived from the actual braid representation,
while the direct field may be rounded or estimated.

**Flagging**: Set `tie_break_applied = True`

## Measurement Precision Standards

### Crossing Number

- **Precision**: Integer value (exact)
- **Source**: Direct from Knot Atlas
- **Validation**: Must be > 0 and <= 13 for this dataset

### Braid Index

- **Precision**: Integer value (exact when from braid word, estimated otherwise)
- **Source**: Braid word preferred, DT code second
- **Constraint**: Must satisfy `braid_index <= crossing_number`
- **Lower Bound**: `braid_index >= 2` for non-trivial knots

### Hyperbolic Volume

- **Precision**: 6 decimal places
- **Source**: Knot Atlas hyperbolic volume field
- **Validation**: Must be >= 0
- **Missing**: Set to `null` when not available

### Alternating Classification

- **Precision**: Boolean (True/False)
- **Source**: Knot Atlas alternating field
- **Ambiguous Cases**: Per FR-010 and T043a, mark as 'unclassifiable' if
 classification is ambiguous (handled in validator.py)

## Implementation Notes

The parser implementation in `code/data/parser.py` follows these rules:

1. **KnotParser.extract_braid_index()**: Implements the priority order
2. **ParsedKnotData.tie_break_applied**: Flag set when tie-breaking occurs
3. **ParsedKnotData.representation_source**: Records which source was used
4. **verify_parser_consistency()**: Validates constraint `braid_index <= crossing_number`

## Verification

The tie-breaking validator script in `code/reproducibility/tie_breaking_validator.py`
(Task T030b) verifies that:

1. All tie-breaking decisions follow the priority order
2. Constraint violations are flagged
3. Tie-break percentage is documented

Exit code 0 indicates all tie-breaking rules were applied consistently.

## References

- FR-011: Measurement precision standards
- Constitution Principle VI: Invariant verification
- SC-007: Tie-breaking rule consistency
- T030: Tie-breaking rules documentation
- T030b: Tie-breaking validation script
- T043a: Ambiguous classification handling
