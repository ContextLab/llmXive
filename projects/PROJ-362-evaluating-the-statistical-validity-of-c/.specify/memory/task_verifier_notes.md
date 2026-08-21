# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was presented showing that the directory `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/` actually exists or contains any files; the claim is unsubstantiated. The required project root folder is missing from the provided artifacts.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, pre‑commit hooks, or related scripts) are present in the provided evidence. The artifacts shown pertain only to the statistical validity feature and do not demonstrate that Ruff and Black have been set up for the project. The required linting/formatting setup is therefore missing.
- **T004** — No `data_loader.py` file or its contents were presented, so we cannot confirm that it fetches TREC Robust and Web data with retry logic, includes NIST archive fallbacks, or enforces CPU‑only execution as required. The necessary artifact is missing.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No `metrics.py` file or its contents were provided; therefore there is no evidence of CPU‑only NDCG@10 or MAP functions with IDCG normalization and explicit relevance‑label mapping. The required artifact is missing, so the task is not satisfied.
- **T017** — No CSV files were presented in the evidence; there is no `results/null_distributions/` directory containing non‑empty files with the required headers `query_id, metric, score`. The implementer must provide the actual null‑distribution CSV artifacts to satisfy the task.
- **T021** — No `power_analysis.py` (or any related code, data, or output files) was provided for inspection, so we cannot confirm that MDES logic was implemented or that the required permutation, power analysis, and reporting functionality exists. The necessary artifact is missing.
- **T023** — No code artifact (e.g., an updated `power_analysis.py` with Benjamini‑Hochberg correction applied separately to NDCG and MAP p‑value families) was provided, nor any test output or documentation showing the correction in action. Without concrete evidence of the implementation, the task requirement is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: results/sensitivity/alpha_sweep.csv
- **T026** — declared artifact(s) missing/empty/invalid: results/p_values/corrected_p_values.csv
