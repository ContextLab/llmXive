# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The `compute_eigenstates` and `compute_lyapunov_exponents` functions correctly instantiate `NumericalLogger` and call `log_residual` as required, but the required output file `data/metadata/residuals.json` does not exist, indicating that the logging integration does not produce the mandated JSON‑lines file. The task is therefore not fully satisfied.
- **T015** — The provided `data/processed/scaling_fits.json` is not a list of objects with the required fields (`disorder_width`, `xi`, `uncertainty`, `p_value`) – it is a dict of empty objects, violating the schema contract. Moreover, the required output file `data/processed/bonferroni_results.json` does not exist. Hence the task’s core processing and output are missing.
