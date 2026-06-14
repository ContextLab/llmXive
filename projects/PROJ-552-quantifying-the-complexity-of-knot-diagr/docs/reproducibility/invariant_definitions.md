# Invariant Definitions and Verification Procedure

## Overview

This document establishes the verification procedure for computed knot invariants against established mathematical definitions from primary literature, as required by **Constitution Principle VI**.

## Scope and Distinction

### Tabulated Core Invariants (Phase 1)

Per **FR-003** and **SC-008**, the following core invariants are **TABULATED** from Knot Atlas rather than computed algorithmically:

| Invariant | Source | Verification Method |
|-----------|--------|---------------------|
| Crossing Number | Knot Atlas | Cross-reference with KnotInfo |
| Braid Index | Knot Atlas | Cross-reference with KnotInfo |

These tabulated values do not require algorithmic validation in Phase 1. Validation of tabulation accuracy is performed via cross-reference against KnotInfo as documented in `docs/reproducibility/core_invariants_tabulation.md`.

### Computed Additional Invariants (Phase 2+)

The following additional invariants require **algorithmic verification** against primary mathematical literature. These will be computed in Phase 2 and beyond:

| Invariant | Computed In | Verification Reference |
|-----------|-------------|------------------------|
| Arc Index | Phase 2+ | See Section 3.1 |
| Seifert Circle Count | Phase 2+ | See Section 3.2 |
| Bridge Number | Phase 2+ | See Section 3.3 |

## Verification Procedure

For each computed additional invariant, the following verification procedure must be executed:

1. **Reference Identification**: Document the primary mathematical literature source defining the invariant
2. **Algorithm Implementation**: Implement the computation algorithm following the mathematical definition
3. **Cross-Validation**: Compare computed values against known values from Knot Atlas or KnotInfo where available
4. **Edge Case Testing**: Verify behavior on canonical knot examples with known invariant values
5. **Documentation**: Record verification results in `docs/reproducibility/algorithm_validation.md`

## Additional Invariant References

### 3.1 Arc Index

**Mathematical Definition**: The arc index of a knot is the minimum number of arcs in an arc presentation of the knot.

**Primary Literature Reference**:
- Dynnikov, I. A. (2006). "Arc-presentations of links: Monotonic simplification". *Proceedings of the London Mathematical Society*, 92(3), 745-766.
- Bae, Y., & Park, W. (2000). "An upper bound of arc index of links". *Mathematics Proceedings of the Edinburgh Mathematical Society*, 43(2), 263-274.

**Verification Requirement**: Implementation must reproduce arc index values for knots with known arc indices from Dynnikov's census.

### 3.2 Seifert Circle Count

**Mathematical Definition**: The number of Seifert circles obtained by applying Seifert's algorithm to an oriented knot diagram.

**Primary Literature Reference**:
- Seifert, H. (1934). "Über das Geschlecht von Knoten". *Mathematische Annalen*, 110(1), 571-592.
- Murasugi, K. (1996). *Knot Theory and Its Applications*. Birkhäuser. Chapter 6.

**Verification Requirement**: For alternating knots, the minimum Seifert circle count equals the braid index (Murasugi's Theorem) [UNRESOLVED-CLAIM: c_b101f99c — status=not_enough_info]. This provides a verification check for alternating knot diagrams.

### 3.3 Bridge Number

**Mathematical Definition**: The bridge number of a knot is the minimum number of bridges (maximal overcrossings) in any bridge presentation of the knot.

**Primary Literature Reference**:
- Schubert, H. (1954). "Über eine numerische Knoteninvariante". *Mathematische Zeitschrift*, 61(1), 245-288.
- Burde, G., & Zieschang, H. (2003). *Knots*. De Gruyter. Chapter 10.

**Verification Requirement**: Bridge number must satisfy the inequality: bridge number ≤ crossing number [UNRESOLVED-CLAIM: c_797199c3 — status=refuted]. For 2-bridge knots, verification against the Schubert normal form is required.

## Constitution Principle VI Compliance

This document satisfies **Constitution Principle VI** by:

1. Explicitly distinguishing between tabulated (core) and computed (additional) invariants
2. Providing primary literature references for all computed additional invariants
3. Establishing a verification procedure that will be executed in Phase 2+
4. Defining clear verification requirements for each additional invariant

## Cross-References

- Tabulated invariant validation: `docs/reproducibility/core_invariants_tabulation.md`
- Algorithm validation (Phase 2+): `docs/reproducibility/algorithm_validation.md`
- Data quality flags: `code/data/validator.py` (implements `MissingInvariantFlag` for uncomputed invariants)
- Hashing and state tracking: `code/reproducibility/hashing.py` (records artifact hashes per Constitution Principle V)

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-XX | PROJ-552 Team | Initial implementation for Constitution Principle VI |