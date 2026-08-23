# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021** — The repository contains `code/models/rsa.py` with a generic dissimilarity function, but it never loads ROI timecourses (T013) or semantic covariates (T008), nor does it generate or write the required `results/rsa_matrices.json` file with the `{roi: {early_late: float, early_early: float}}` schema. The expected output file is missing entirely.
- **T022** — The repository contains a `stats.py` with a permutation test (default 1000 iterations) and an FDR‑correction helper, but the required output file `results/permutation_pvalues.json` is absent, so the task’s specified artifact is missing.
- **T024** — The `code/utils/viz.py` file is truncated and the `plot_early_late_roi_comparison` function ends abruptly, indicating the visualization code is not fully implemented. Moreover, the required output file `results/rsa_heatmaps.png` does not exist. Both the functional artifact and the expected result are missing, so the task is not satisfied.
- **T031** — No code, notebook, script, or output files implementing a 5‑fold cross‑validation and reporting accuracy versus a chance baseline are present. The required artifact is missing, so the task is not satisfied.
