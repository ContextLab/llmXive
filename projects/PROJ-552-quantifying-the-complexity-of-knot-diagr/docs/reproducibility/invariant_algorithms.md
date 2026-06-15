# Knot Invariant Algorithms and Mathematical Definitions

This document provides mathematical definitions, algorithmic descriptions, and
reference implementations for all knot invariants used in this research project,
per FR-003 requirements for invariant documentation and Constitution Principle VI
verification against established mathematical definitions from primary literature.

---

## 1. Overview

This project quantifies knot complexity using two core invariants:
- **Crossing Number (c)**: The minimum number of crossings in any diagram of the knot
- **Braid Index (b)**: The minimum number of strands in any braid representation

Additional invariants are computed for extended analysis:
- **Arc Index (α)**: The minimum number of arcs in an arc presentation
- **Seifert Circle Count (s)**: The number of Seifert circles in the Seifert algorithm
- **Bridge Number (β)**: The minimum number of local maxima in any diagram

**Note on Core Invariants**: Per FR-003 and SC-008, crossing number and braid index
are TABULATED from the Knot Atlas ({{claim:c_3ea0f57a}}) rather than computed by
algorithm. Algorithm validation per Constitution Principle VI applies only to the
additional invariants computed in Phase 2+.

---

## 2. Crossing Number (c)

### 2.1 Mathematical Definition

The crossing number \( c(K) \) of a knot \( K \) is defined as:

\[ c(K) = \min \{ \text{crossings}(D) \mid D \text{ is a diagram of } K \} \]

where the minimum is taken over all possible diagrams \( D \) representing the knot \( K \).

**Reference**: Adams, C. C. (2004). *The Knot Book: An Elementary Introduction to the
Mathematical Theory of Knots*. American Mathematical Society. Section 2.2.

### 2.2 Tabulation Source

For this project, crossing numbers are obtained from the Knot Atlas via:
- **Source**: {{claim:c_3ea0f57a}} (Wikidata Q16963570)
- **URL**: https://katlas.org
- **Coverage**: All prime knots with crossing number ≤ 13
- **Validation**: Cross-validated against KnotInfo reference values (T026)

### 2.3 Computational Considerations

Computing crossing number is NP-hard for general knots. [UNRESOLVED-CLAIM: c_236ede6a — status=not_enough_info] For prime knots with c ≤ 13,
tabulated values from the Knot Atlas provide the authoritative reference.

---

## 3. Braid Index (b)

### 3.1 Mathematical Definition

The braid index \( b(K) \) of a knot \( K \) is defined as:

\[ b(K) = \min \{ n \mid K \text{ is the closure of an } n\text{-strand braid} \} \]

**Reference**: Yamada, S. (1987). "The minimal number of Seifert circles equals the
braid index of a knot." *Inventiones mathematicae* 89(2): 347-356.

### 3.2 Fundamental Inequality

For any knot \( K \):

\[ b(K) \leq c(K) \]

This constraint is acknowledged in all analyses (see docs/reproducibility/mathematical_constraints.md).

### 3.3 Yamada's Theorem

The braid index equals the minimum number of Seifert circles over all diagrams [UNRESOLVED-CLAIM: c_57e4614a — status=not_enough_info]:

\[ b(K) = \min_D s(D) \]

where \( s(D) \) is the number of Seifert circles in diagram \( D \).

**Reference**: Yamada, S. (1987) as cited above.

### 3.4 Tabulation Source

For this project, braid indices are obtained from the Knot Atlas via:
- **Source**: {{claim:c_3ea0f57a}} (Wikidata Q16963570)
- **URL**: https://katlas.org
- **Validation**: Cross-validated against KnotInfo reference values (T026)

---

## 4. Arc Index (α)

### 4.1 Mathematical Definition

The arc index \( \alpha(K) \) of a knot \( K \) is defined as:

\[ \alpha(K) = \min \{ \text{arcs}(P) \mid P \text{ is an arc presentation of } K \} \]

An arc presentation represents a knot as a collection of arcs in half-planes
meeting at a common axis.

**Reference**: Cromwell, P. R. (1995). "Embedding knots and links in an open book.
I. Basic properties." *Topology and its Applications* 64(1): 37-58.

### 4.2 Relationship to Crossing Number

For non-trivial knots:

\[ \alpha(K) \leq c(K) + 2 \]

**Reference**: Bae, Y., & Park, C. (2000). "An upper bound of arc index of links."
*Mathematical Proceedings of the Cambridge Philosophical Society* 129(3): 491-500.

### 4.3 Reference Algorithm

**Input**: Knot diagram D
**Output**: Arc index α(K)

```
Algorithm: Compute Arc Index
1. Generate all arc presentations of D
2. For each presentation, count the number of arcs
3. Return the minimum arc count

Complexity: Exponential in crossing number
Practical approach: Use existing tabulations for c ≤ 13
```

---

## 5. Seifert Circle Count (s)

### 5.1 Mathematical Definition

The Seifert circle count \( s(D) \) for a diagram \( D \) is the number of disjoint
simple closed curves obtained by applying Seifert's algorithm:

1. Orient the knot diagram
2. At each crossing, smooth according to orientation (resolve crossing)
3. Count the resulting disjoint circles

**Reference**: Seifert, H. (1934). "Über das Geschlecht von Knoten." *Mathematische
Annalen* 110(1): 571-592.

### 5.2 Seifert's Algorithm

```
Algorithm: Seifert Circle Computation
Input: Oriented knot diagram D
Output: Number of Seifert circles s(D)

1. Parse crossings with orientation information
2. For each crossing, apply smoothing:
 - If over-strand goes left-to-right, connect incoming from bottom to outgoing top
 - If over-strand goes right-to-left, connect incoming from top to outgoing bottom
3. Trace connected components (circles)
4. Return count of components
```

### 5.3 Relationship to Braid Index

Per Yamada's Theorem (Section 3.3):

\[ b(K) = \min_D s(D) \]

This provides a computational pathway to braid index estimation.

---

## 6. Bridge Number (β)

### 6.1 Mathematical Definition

The bridge number \( \beta(K) \) of a knot \( K \) is defined as:

\[ \beta(K) = \min \{ \text{maxima}(D) \mid D \text{ is a diagram of } K \} \]

where maxima are local maxima with respect to a chosen height function.

**Reference**: Schubert, H. (1954). "Über eine numerische Knoteninvariante."
*Mathematische Zeitschrift* 61(1): 245-288.

### 6.2 Bridge Decomposition

A knot has bridge number β if it can be decomposed into β over-arches and β
under-arches. The trivial knot has β = 1 [UNRESOLVED-CLAIM: c_d342705f — status=not_enough_info].

### 6.3 Relationship to Crossing Number

For any non-trivial knot:

\[ \beta(K) \leq \frac{c(K)}{2} + 1 \]

**Reference**: Murasugi, K. (1996). *Knot Theory and Its Applications*. Birkhäuser.
Theorem 9.3.2.

---

## 7. Hyperbolic Volume (vol)

### 7.1 Mathematical Definition

For hyperbolic knots, the hyperbolic volume is the volume of the knot complement
\( S^3 \setminus K \) endowed with its unique complete hyperbolic metric of finite
volume.

**Reference**: Thurston, W. P. (1982). "Three-dimensional manifolds, Kleinian groups
and hyperbolic geometry." *Bulletin of the American Mathematical Society* 6(3):
357-381.

### 7.2 Classification Criterion

A knot is **hyperbolic** if and only if its complement admits a complete hyperbolic
metric of finite volume. This is equivalent to:

\[ \text{vol}(K) > 0 \]

**Reference**: Perelman, G. (2002-2003). Geometrization of 3-manifolds.

### 7.3 Tabulation Source

For this project, hyperbolic volumes are obtained from the Knot Atlas via:
- **Source**: {{claim:c_3ea0f57a}} (Wikidata Q16963570)
- **URL**: https://katlas.org
- **Validation**: Cross-validated against KnotInfo reference values (T040)
- **Filtering**: Non-hyperbolic knots excluded per FR-012 (T019)

---

## 8. Alternating Classification

### 8.1 Mathematical Definition

A knot diagram is **alternating** if the crossings alternate between over and under
as one traverses the knot. A knot is alternating if it admits an alternating diagram.

**Reference**: Tait, P. G. (1884). "On the division of knots into two classes."
*Proceedings of the Royal Society of Edinburgh* 11: 319-322.

### 8.2 Alternating Property

For alternating knots:
- The crossing number is realized by any reduced alternating diagram
- **Tait's First Conjecture**: Proved by Menasco and Thistlethwaite (Menasco–Thistlethwaite (2210.03720, https://arxiv.org/abs/2210.03720))

### 8.3 Classification Handling

Per FR-010 and T043a, knots with ambiguous alternating/non-alternating classification
are either excluded or marked as 'unclassifiable' with appropriate flagging.

---

## 9. Primary Literature References

| Invariant | Primary Reference | Year |
|-----------|-------------------|------|
| Crossing Number | Adams, C. C. *The Knot Book* | 2004 |
| Braid Index | Yamada, S. *Inventiones math.* | 1987 |
| Arc Index | Cromwell, P. R. *Topology Appl.* | 1995 |
| Seifert Circles | Seifert, H. *Math. Ann.* | 1934 |
| Bridge Number | Schubert, H. *Math. Z.* | 1954 |
| Hyperbolic Volume | Thurston, W. P. *BAMS* | 1982 |
| Alternating Knots | Tait, P. G. *Proc. Roy. Soc.* | 1884 |

---

## 10. Implementation Notes

### 10.1 Tabulated vs. Computed Invariants

| Invariant | Status | Source |
|-----------|--------|--------|
| Crossing Number | TABULATED | Knot Atlas |
| Braid Index | TABULATED | Knot Atlas |
| Hyperbolic Volume | TABULATED | Knot Atlas |
| Alternating | TABULATED | Knot Atlas |
| Arc Index | COMPUTED | Algorithm (Phase 2+) |
| Seifert Circle Count | COMPUTED | Algorithm (Phase 2+) |
| Bridge Number | COMPUTED | Algorithm (Phase 2+) |

### 10.2 Validation Requirements

Per Constitution Principle VI:
- All computed invariants must be validated against established mathematical definitions
- Tabulated invariants must be validated against KnotInfo reference values
- Documentation must cite primary literature for all invariants

### 10.3 Algorithm Validation Timeline

- **Phase 1 (US1)**: Tabulation validation only (T026)
- **Phase 2+**: Algorithm validation for additional invariants (SC-010)

---

## 11. Reproducibility Checklist

- [x] Mathematical definitions documented with formula citations
- [x] Primary literature references provided for all invariants
- [x] Tabulation sources specified (Knot Atlas, {{claim:c_3ea0f57a}})
- [x] Algorithm descriptions provided for computable invariants
- [x] Distinction between tabulated and computed invariants clarified
- [x] Constitution Principle VI compliance documented

---

*Document generated per FR-003 invariant algorithm documentation requirements.*
*Last updated: 2026-01-15*