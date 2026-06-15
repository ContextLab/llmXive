# Uncomputable Invariants Log

**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Task**: T051 - Log uncomputable invariants (per FR-003)
**Generated**: 2026-06-02
**Status**: Current Phase 1 Complete

---

## Overview

This document logs all knot invariants that could not be computed during the analysis pipeline execution, per FR-003 requirements for invariant computation tracking and transparency.

---

## Invariant Computation Status Summary

| Invariant | Computation Method | Status | Notes |
|-----------|-------------------|--------|-------|
| Crossing Number | Tabulated from {{claim:c_3ea0f57a}} | ✅ Available | Per FR-003/SC-008, tabulated not computed |
| Braid Index | Tabulated from {{claim:c_3ea0f57a}} | ✅ Available | Per FR-003/SC-008, tabulated not computed |
| Hyperbolic Volume | Tabulated from {{claim:c_3ea0f57a}} | ✅ Available | Validated against KnotInfo (T040) |
| Alternating Classification | Tabulated from {{claim:c_3ea0f57a}} | ✅ Available | Validated per FR-010 (T043a) |
| Arc Index | Algorithmic computation | ⏳ Deferred | Phase 2+ per SC-010 |
| Seifert Circle Count | Algorithmic computation | ⏳ Deferred | Phase 2+ per SC-010 |
| Bridge Number | Algorithmic computation | ⏳ Deferred | Phase 2+ per SC-010 |

---

## Uncomputable Invariants Details

### 1. Arc Index

**Reason for Non-Computation**: Per SC-010, algorithmic validation of additional invariants (arc index, Seifert circle count, bridge number) is deferred to Phase 2+.

**Current Status**: No arc index computation implemented in Phase 1. All arc index values marked as `null` in processed data.

**Data Impact**: 0% coverage in current dataset. This does not affect core analysis as arc index is not required for primary correlation analysis (crossing number vs. braid index vs. hyperbolic volume).

**Future Work**: Implementation planned for Phase 2+ with algorithm validation per Constitution Principle VI (T026a).

### 2. Seifert Circle Count

**Reason for Non-Computation**: Per SC-010, algorithmic validation of additional invariants is deferred to Phase 2+.

**Current Status**: No Seifert circle count computation implemented in Phase 1. All values marked as `null` in processed data.

**Data Impact**: 0% coverage in current dataset. Not required for primary analysis objectives.

**Future Work**: Implementation planned for Phase 2+ with algorithm validation per Constitution Principle VI.

### 3. Bridge Number

**Reason for Non-Computation**: Per SC-010, algorithmic validation of additional invariants is deferred to Phase 2+.

**Current Status**: No bridge number computation implemented in Phase 1. All values marked as `null` in processed data.

**Data Impact**: 0% coverage in current dataset. Not required for primary analysis objectives.

**Future Work**: Implementation planned for Phase 2+ with algorithm validation per Constitution Principle VI.

---

## Core Invariants (Tabulated, Not Computed)

Per FR-003 and SC-008, the following core invariants are **tabulated** from the knot atlas rather than computed:

- **Crossing Number**: Tabulated from {{claim:c_3ea0f57a}} (Wikidata Q16963570)
- **Braid Index**: Tabulated from {{claim:c_3ea0f57a}}
- **Hyperbolic Volume**: Tabulated from {{claim:c_3ea0f57a}}
- **Alternating/Non-Alternating Classification**: Tabulated from {{claim:c_3ea0f57a}}

**Validation**: Core invariant tabulation accuracy validated in T026 (core_invariants_tabulation.md) with ≥90% match against KnotInfo reference values.

**Algorithm Validation**: Constitution Principle VI (T026a) applies only to **computed** invariants in Phase 2+, not to tabulated core invariants in Phase 1.

---

## Data Quality Flags Applied

The following data quality flags were applied to track invariant availability (per T009, T010, T029):

| Flag Type | Applied To | Count |
|-----------|------------|-------|
| `missing_invariant_flags` | Arc index, Seifert circle count, bridge number | All records (N/A for Phase 1) |
| `data_quality_flags` | Format failures, null values in core invariants | 0 (all core invariants present) |
| `ambiguous_classification_flags` | Knots with unclear alternating classification | 0 (all classified) |

---

## Exclusion Log

Knots excluded due to uncomputable invariants:

| Exclusion Reason | Count | Documentation |
|---------------------|-------|---------------|
| Hyperbolic volume = 0 (non-hyperbolic) | Logged in excluded_knots.md (T019) | docs/reproducibility/excluded_knots.md |
| Missing crossing number | 0 | All records have crossing number |
| Missing braid index | 0 | All records have braid index |
| Missing hyperbolic volume | 0 | All records have hyperbolic volume |

**Note**: The hyperbolic filter (T019) excludes non-hyperbolic knots (volume = 0), but this is a **filtering decision** per FR-012, not an uncomputable invariant. Excluded knots are logged in `docs/reproducibility/excluded_knots.md`.

---

## Verification Status

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FR-003: Log uncomputable invariants | ✅ Complete | This document |
| SC-008: Invariant coverage documentation | ⏳ Pending | T052 (invariant_coverage.md) |
| SC-010: Phase 2+ algorithm validation | ⏳ Pending | Phase 2+ implementation |
| Constitution Principle VI: Invariant definition verification | ✅ Documented | T026a (invariant_definitions.md) |

---

## Reproducibility Artifacts

This log is part of the FR-007 required reproducibility documentation:

- **Checksum**: SHA-256 recorded in `data/` directory and `docs/reproducibility/checksums.md` (T044, T045)
- **Operation Log**: Recorded in `docs/reproducibility/operation_logs.md` (T049)
- **Derivation Notes**: Formula citations and transformation logic in `docs/reproducibility/derivation_notes.md` (T046)
- **Validation Status**: Overall validation status in `docs/reproducibility/validation_status.md` (T053)

---

## References

- **FR-003**: Invariant computation requirements and tabulation sources
- **SC-008**: Invariant coverage requirements
- **SC-010**: Phase 2+ algorithm validation reservation
- **Constitution Principle VI**: Invariant definition verification against primary literature
- **{{claim:c_3ea0f57a}}**: Knot Atlas tabulation source (Wikidata Q16963570)

---

## Update History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-06-02 | 1.0 | Initial log creation | T051 implementation |

---

*End of Uncomputable Invariants Log*