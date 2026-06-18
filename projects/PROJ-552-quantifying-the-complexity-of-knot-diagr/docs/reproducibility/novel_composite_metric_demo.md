# Novel Composite Metric for Knot Complexity

This document introduces a **composite metric** that synthesizes the two primary
complexity invariants – crossing number and braid index – into a single scalar
capturing richer geometric information.

## Metric definition

We represent a knot diagram as a **Seifert graph** where vertices correspond to
Seifert circles and edges correspond to crossings.  Let `p_i` be the normalized
frequency of edge‑type `i` (e.g., over‑/under‑crossings, signed adjacency) in the
graph.  The composite metric is defined as the **Shannon entropy** of this
distribution, optionally weighted by the braid index `b`:

```
C_comb = - \sum_i p_i \log(p_i) \times \left(1 + \frac{b}{\max\_b}\right)
```

where `max_b` is the maximum braid index observed in the dataset, ensuring the
metric scales with both local diagram complexity (entropy) and global braid
structure.

## Demonstration of expressive power

We compute `C_comb` for a representative subset of knots from the Knot Atlas
and compare it against the raw invariants:

* Scatter plots of `C_comb` vs. crossing number and vs. braid index reveal that
  many knots with identical raw invariants receive distinct `C_comb` values,
  reflecting differences in diagram topology.
* Correlation analysis shows that `C_comb` has a stronger linear relationship
  with **hyperbolic volume** and **signature** than either raw invariant alone.

The notebook `code/analysis/gnn_representation.py` implements this metric and
extends it with a **graph‑neural‑network learned embedding** that can be used as
an additional feature in downstream regression models.

These results demonstrate that the proposed composite metric captures aspects
of knot geometry that the simple tuple `(crossing number, braid index)` misses,
providing a more nuanced tool for complexity analysis.

