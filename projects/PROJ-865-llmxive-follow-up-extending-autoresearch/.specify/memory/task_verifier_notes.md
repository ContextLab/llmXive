# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T083** — No execution logs, metric files, or any other artifacts showing that the rule engine and baseline agent were run on the 10‑item subset, nor any evidence of data‑flow verification, metric logging, or censored‑data handling is present. The claim lacks the required concrete outputs.
- **T084** — The required script `code/analysis/statistical_model.py` is missing, and the provided output files reference a sample size of 100 despite the input CSV containing only 10 rows, with no evidence of censored‑data handling. Consequently the task’s core execution and verification requirements are not satisfied.
- **T085** — The required output files `data/derived/full_rules_library.json` and `data/derived/full_regression_results.json` are missing, so the full pipeline execution is not demonstrated. The existing `full_results.csv` alone does not satisfy the task’s output requirements.
- **T086** — No research report file or its contents are present; the implementer provided only a textual claim without delivering the compiled document that should contain the hypothesis discussion, interaction term significance, error taxonomy, and sensitivity analysis. The required artifact is missing.
