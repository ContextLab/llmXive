# Creative Composite Metric for Knot Diagram Complexity

The original specification characterizes knot diagram complexity using the
two‑dimensional tuple **(crossing number, braid index)**.  While these
invariants are informative, they capture only limited aspects of the
diagrammatic structure.

## Proposed composite metric

We introduce a *Weighted Entropy Metric* (WEM) that synthesizes multiple
diagram representations into a single scalar value:

1. **Crossing entropy** – compute the Shannon entropy of the distribution of
   crossing types (positive/negative) in the diagram.
2. **Braid entropy** – treat the braid word as a sequence of generators and
   compute the entropy of generator frequencies.
3. **Graph‑theoretic descriptor** – construct the planar graph of the diagram,
   compute its degree distribution entropy.

The final metric is a weighted sum:

```
WEM = α * H_crossing + β * H_braid + γ * H_graph
```

where α, β, γ are non‑negative weights that can be tuned (e.g., via cross‑validation) to maximise correlation with external geometric measures such as hyperbolic volume.

## Implementation sketch

A reference implementation lives in `code/analysis/composite_metric_novel.py`.  The
module provides a function `weighted_entropy_metric(knot_diagram, weights)` that
returns the WEM value for a given diagram.

## Expected benefits

* Captures variability in crossing signs and braid structure beyond raw counts.
* Reflects the topological complexity of the underlying planar graph.
* Enables learning‑based tuning of weights to align with downstream tasks.

Future work includes evaluating the WEM against the existing tuple on downstream
prediction tasks (e.g., hyperbolic volume regression) to demonstrate its added
expressiveness.

