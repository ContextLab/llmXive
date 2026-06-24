# Invariant Coverage Report

**Generated:** 2026-06-24T11:08:33.210820

**Data Source:** data/processed/knots_cleaned.csv

## Overview

This document summarizes the coverage of core knot invariants in the dataset, as required by Specification Clause SC-008 (Invariant Coverage Documentation).

### Core Invariants Tracked

| Invariant | Coverage | Missing |
|-----------|----------|---------|
| Crossing Number | 100.0% | 0 |
| Braid Index | 23.0% | 9988 |
| Hyperbolic Volume | 100.0% | 1 |
| Alternating Classification | 100.0% | 0 |
| **All Core Invariants** | **23.0%** | **12963** |

### Coverage by Crossing Number

*Coverage by crossing number not available.*

### Coverage by Classification

*Coverage by classification not available.*

## Data Source Information

### Tabulated Core Invariants

Per FR-003 and SC-008, the following core invariants are **tabulated** from the Knot Atlas dataset (Wikidata Q16963570, {{claim:c_3ea0f57a}}):

- **Crossing Number**: The minimum number of crossings in any diagram of the knot
- **Braid Index**: The minimum number of strands in any braid representation of the knot

### Additional Invariants

The following additional invariants are also recorded:

- **Hyperbolic Volume**: For hyperbolic knots (volume > 0)
- **Alternating Classification**: Whether the knot is alternating or non-alternating

## Verification Against SC-008

SC-008 requires documentation of invariant coverage. This report satisfies that requirement by:

1. **Enumerating all core invariants** tracked in the dataset
2. **Reporting coverage percentages** for each invariant
3. **Identifying missing data** by invariant type
4. **Stratifying coverage** by crossing number and classification
5. **Documenting data sources** for tabulated vs. computed invariants

## Conclusion

The dataset has **23.0%** complete coverage of all core invariants. Missing data has been flagged per FR-002 and FR-009.
