# Braid Index Precision Measurement Standards

The braid index is a more delicate invariant than the crossing number and
its empirical determination can be affected by diagram selection, projection
choices, and algorithmic heuristics.  To ensure that reported braid‑index
values are comparable across studies, we adopt the following precision
framework:

1. **Dataset stratification** – Prime knots are grouped by crossing number
   ranges (e.g., 3‑6, 7‑10, 11‑14, …).  Within each stratum we compute the
   braid index for *all* available minimal diagrams.
2. **Repeated computation** – For each knot we run the braid‑index estimator
   on at least three independent diagram representations and record the
   variance.
3. **Confidence reporting** – The reported braid index is the mode of the
   repeated runs; a ±1 confidence interval is provided when the variance
   exceeds zero.
4. **Cross‑validation** – Results are cross‑checked against the
   *Knot Atlas* database and the *KnotInfo* tables where available.

These standards are applied in the `braid_index_precision` analysis
pipeline and the results are documented in `docs/reproducibility/braid_index_precision_evidence.md`.
