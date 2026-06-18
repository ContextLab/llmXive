# Braid Index Precision Across Prime Knot Classes

The braid index of a knot is defined as the minimal number of strands required
to represent the knot as a closed braid. While the crossing number is
deterministically computed from the diagram, estimating the braid index
experimentally involves algorithmic searches that may yield different results
depending on the knot family and the complexity of the diagram.

## Precision Standard

To establish a rigorous standard of evidence for braid‑index measurements we
adopt the following protocol:

1. **Multiple Independent Computations** – For each prime knot we compute the
   braid index using at least three distinct algorithms (e.g., Morton's
   inequality‑based approach, the Birman–Menasco algorithm, and a
   heuristic‑search method). The reported braid index is the consensus value
   agreed upon by a majority of methods.
2. **Cross‑Family Validation** – Knots are grouped by crossing number ranges
   (e.g., 3‑6, 7‑10, 11‑14, …). Within each group we report the standard
   deviation of braid‑index estimates across the algorithms. This quantifies
   the precision of our measurements for that class.
3. **Threshold for Acceptance** – A braid‑index measurement is accepted if the
   inter‑algorithm standard deviation is ≤ 0.5 for the corresponding class.
   Values exceeding this threshold trigger a manual review and possible
   re‑computation with increased algorithmic depth.

## Evidence

The file `data/plots/crossing_vs_braid.png` visualises the distribution of braid
indices across crossing numbers and includes error bars representing the
standard deviation within each class. Detailed numerical tables are provided in
`data/processed/braid_index_precision_report.json`.

By adhering to this protocol we ensure that braid‑index measurements are
comparable in precision to crossing‑number counts, satisfying the reviewer’s
request for a clear standard of evidence.
