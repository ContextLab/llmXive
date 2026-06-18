# Precision of Braid Index Measurements

The braid index of a knot is an integer invariant that can be computed
algorithmically, but the computation may be sensitive to the representation
of the knot diagram and to the heuristic choices made by the algorithm.
To provide a rigorous standard of evidence for the braid‑index component of
our complexity metric, we adopt the following validation protocol:

1. **Reference Dataset** – We use the curated `knots_validated.csv` dataset,
   which contains prime knots up to 12 crossings with braid indices verified
   against the Knot Atlas and the KnotInfo tables.
2. **Cross‑Class Evaluation** – For each class of prime knots (by crossing
   number), we compute the braid index for all members and report the
   *precision* as the proportion of knots whose computed index matches the
   reference value.
3. **Confidence Intervals** – Assuming a binomial model, we report a 95 %
   Wilson confidence interval for the precision of each crossing‑class.
4. **Re‑computation Audits** – The computation is performed independently
   with two different implementations (the `braid_index` routine in
   `code/analysis/composite_metric.py` and the external SageMath routine).
   Discrepancies trigger a manual review and are logged in
   `docs/reproducibility/ambiguous_classification_log.md`.

The results of this validation are stored in `data/processed/braid_index_precision.json`
and visualised in `data/plots/braid_index_precision.png`.  These artifacts are
referenced in the main specification (see the *Complexity Metrics* section) to
demonstrate the reproducibility and statistical reliability of the braid‑index
measure across all investigated knot classes.

