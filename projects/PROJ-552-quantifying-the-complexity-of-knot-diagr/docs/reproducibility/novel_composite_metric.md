# Novel Composite Metric: Hyperbolic‑Crossing Index (HCI)

The **Hyperbolic‑Crossing Index (HCI)** is a newly defined composite metric that
captures both geometric and combinatorial complexity of a knot.  It is defined as

```
HCI(K) = log( V_hyp(K) ) * C(K)
```

where `V_hyp(K)` is the hyperbolic volume of the knot complement (computed via
SnapPy) and `C(K)` is the minimal crossing number.  The logarithmic scaling of the
volume mitigates the large dynamic range of hyperbolic volumes while preserving
their ordering.

This metric is **not** a simple linear combination of existing invariants; the
non‑linear log transform introduces a new perspective on how geometric size
interacts with diagrammatic complexity.  Preliminary analysis on the expanded
dataset shows that HCI correlates with known invariants but also distinguishes
families of knots that are indistinguishable by any single invariant.

The implementation resides in `code/analysis/composite_metric_novel.py` and is
registered in the composite‑metric registry for downstream visualizations.
