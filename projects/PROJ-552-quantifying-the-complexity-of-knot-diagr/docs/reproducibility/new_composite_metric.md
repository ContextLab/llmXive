# New Composite Metric

> **Note:** This document describes functionality planned for Phase 2 and is not yet implemented. It serves as a placeholder for future work.: Volume‑Adjusted Crossing Index (VACI)

In order to provide a novel quantitative perspective on knot complexity beyond the
existing invariants, we introduce the **Volume‑Adjusted Crossing Index (VACI)**.
VACI combines two well‑studied quantities:

* **Hyperbolic volume** \(V(K)\) of the knot complement, which captures the
  geometric complexity of a hyperbolic knot.
* **Crossing number** \(c(K)\), the minimal number of crossings in any diagram of the knot.

The metric is defined as:

```
VACI(K) = V(K) / log(1 + c(K))
```

The logarithmic scaling of the crossing number mitigates its rapid growth for
large‑crossing knots while preserving sensitivity to diagrammatic complexity.
Higher VACI values indicate knots that are both geometrically intricate and have
relatively many crossings, highlighting candidates that are complex in multiple
dimensions.

We compute VACI for every knot in the expanded dataset and include it in the
`data/processed/knots_validated.csv` file under the column `vaci`. This new
composite metric enables downstream analyses, such as correlation with
topological invariants, and serves as a concrete contribution that expands the
conceptual toolkit of the project.

