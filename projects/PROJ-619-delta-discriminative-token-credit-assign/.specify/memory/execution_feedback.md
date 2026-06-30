# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely CANNOT be measured on a CPU (it needs a GPU), do NOT fake it — measure a different, genuinely-computable proxy and name it honestly, or report that the metric is unmeasurable here. Never present a simulated number as a measurement.

- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…. 2.  **Data Proxy**: We generate synthetic token-gradient vectors.…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…**Scale**:     *   5,000 synthetic samples (tokens).     *   1,000…”
- code/delta_proxy.py: synthetic/fake INPUT data not authorized by the spec — “…scrim=2000):     """     Generates synthetic token-gradient vectors m…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/README.md: synthetic/fake INPUT data not authorized by the spec — “…. 2.  **Data Proxy**: We generate synthetic token-gradient vectors.…”; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…**Scale**:     *   5,000 synthetic samples (tokens).     *   1,000…”; code/delta_proxy.py: synthetic/fake INPUT data not authorized by the spec — “…scrim=2000):     """     Generates synthetic token-gradient vectors m…”

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)
