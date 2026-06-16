# Algorithm Validation Report

## Overview

This document validates the algorithms used to compute knot invariants beyond the core tabulated invariants (crossing number and braid index). Per Constitution Principle VI, all computed invariants must be verified against established mathematical definitions from primary literature.

## Validation Scope

Core invariants (crossing number, braid index) are TABULATED from the Knot Atlas ({{claim:c_3ea0f57a}}) per FR-003 and SC-008. Algorithm validation applies only to ADDITIONAL invariants computed in Phase 2+:

- Arc index
- Seifert circle count
- Bridge number

## Validation Procedure

### Step 1: Reference Literature Collection

For each additional invariant, collect primary mathematical definitions:

| Invariant | Primary Reference | Section/Page |
|-----------|-------------------|--------------|
| Arc index | Adams, "The Knot Book" (1994) | Chapter 9 |
| Seifert circle count | Seifert, "Über das Geschlecht von Knoten" (1934) | §2 |
| Bridge number | Schubert, "Über eine numerische Knoteninvariante" (1954) | Definition 1 |

### Step 2: Algorithm Implementation Review

Each algorithm implementation must:

1. Match the mathematical definition exactly
2. Handle edge cases (unknot, alternating knots, non-alternating knots)
3. Document computational complexity
4. Include test cases with known values

### Step 3: Cross-Validation

Compare computed values against:

- KnotInfo database values (where available)
- OEIS sequences (where applicable)
- Manual verification for small crossing numbers

### Step 4: Discrepancy Resolution

Any discrepancies must be:

1. Logged in docs/reproducibility/uncomputable_invariants.md
2. Investigated for algorithm vs. reference errors
3. Resolved before proceeding to analysis

## Validation Status

| Invariant | Reference Verified | Implementation Verified | Cross-Validation | Status |
|-----------|-------------------|------------------------|------------------|--------|
| Arc index | ✓ | Pending | Pending | Phase 2+ |
| Seifert circle count | ✓ | Pending | Pending | Phase 2+ |
| Bridge number | ✓ | Pending | Pending | Phase 2+ |

## Conclusion

Core invariants are tabulated and do not require algorithm validation. Additional invariants will undergo full validation in Phase 2+ before any analysis proceeds.
