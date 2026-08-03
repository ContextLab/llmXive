# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — declared artifact(s) missing/empty/invalid: data/processed/harmonized.parquet
- **T022** — No code, notebook, or output files implementing Conley standard errors for OLS or HAC/robust SEs for spatial lag/error models were provided; the claim contains only a textual description without any concrete artifact to verify. Consequently the required robust SE calculations and p‑value outputs are missing.
- **T023** — No code, notebook, data file, or report containing the Benjamini‑Hochberg FDR‑adjusted p‑values is present. The implementer did not provide any artifact that shows the correction applied to the robust‑SE p‑values from T022, so the requirement is unmet.
- **T024** — No code, script, or documentation was presented that implements a convergence fallback from spatial models to OLS, nor any evidence that OLS Moran's I is still calculated and reported in that scenario. The required artifact is missing.
- **T025** — No code, test, or documentation was provided showing that the weight matrix generation now catches failures of both Queen and KNN, raises `SpatialWeightMatrixError("Both Queen and KNN failed")`, and logs a CRITICAL error. The required implementation artifact is missing.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T028** — The required artifact `tests/integration/test_validation.py` does not exist on disk, so no integration test for the permutation test logic is present. The task cannot be considered complete until this file is created with the appropriate test implementation.
