# Braid Index Precision – Standards of Evidence

The braid index, unlike the crossing number, is not directly observable from a
diagram and must be inferred using algorithmic or experimental methods.  To
provide a scientifically rigorous measurement we adopt the following standards:

1. **Benchmark against known prime knots** – For each class of prime knots (e.g.,
   up to 12 crossings) we compare computed braid indices with values reported in
   the Knot Atlas and verified by independent implementations.
2. **Statistical confidence** – For each knot we run the braid‑index estimator
   on at least 30 randomly generated diagrammatic representations.  The mean
   value and a 95 % confidence interval are recorded.
3. **Cross‑validation** – Results are cross‑validated using two independent
   algorithms (the Seifert‑surface method and the Morton–Franks‑Williams bound).
4. **Reproducibility logs** – All random seeds, software versions, and
   parameter settings are logged in `docs/reproducibility/seed_verification.md`
   and the full execution trace is stored in `data/logs/reproducibility.log`.

These practices ensure that the reported braid‑index measurements are precise
and comparable across different knot families, satisfying the reviewer’s
request for a clear standard of evidence.
