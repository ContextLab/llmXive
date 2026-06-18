# Innovative Composite Metric for Knot Complexity

The current specification quantifies knot complexity using the two‑dimensional tuple  
`(crossing number, braid index)`. While this captures important combinatorial aspects, it
does not reflect how these invariants interact across different diagrammatic
representations.

We introduce **Weighted Entropy Complexity (WEC)**, a composite metric that
 synthesizes the crossing number and braid index with a topological‑graph‑theoretic
 descriptor derived from the knot diagram’s Seifert graph. For a given knot diagram,
 let `c` be the crossing number, `b` the braid index, and `e` the Shannon entropy of
 the degree distribution of its Seifert graph. The metric is defined as  

```
WEC = α·log(c + 1) + β·log(b + 1) + γ·e
```

where `α, β, γ` are non‑negative weights that can be tuned (e.g., via cross‑validation)
 to maximize correlation with geometric properties such as hyperbolic volume or
 ropelength. Preliminary experiments (see `code/analysis/composite_metric_novel.py`)
 show that WEC explains a larger fraction of variance in hyperbolic volume than the
 raw tuple alone.

Future work will explore learned embeddings from graph‑neural networks to replace the
 entropy term, further enriching the composite descriptor.
