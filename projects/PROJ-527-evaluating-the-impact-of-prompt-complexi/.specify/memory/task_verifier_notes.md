# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019a** — The required `data/processed/prompt_variants.parquet` file is missing, so the implementer could not compute the token deltas as specified. Moreover, the produced `manual_review_queue.csv` has incorrect column names and values (e.g., `sample_id`, `complexity_label`, `token_delta_vs_very_complex`, `flag_reason`) instead of the required `problem_id`, `variant_label`, `token_delta`, `reason`, and the reason strings do not match the mandated values (`token_delta_low` or `degenerate_under_complex`).
- **T020b** — declared artifact(s) missing/empty/invalid: data/results/collinearity_report.csv
- **T020c** — declared artifact(s) missing/empty/invalid: data/results/collinearity_report.csv, data/processed/prompt_variants_transformed.parquet, data/processed/collinearity_status.json
- **T027a** — declared artifact(s) missing/empty/invalid: data/processed/prompt_variants.parquet
- **T027b** — The claim that `static_analysis.py` now contains comments citing McCabe (1976) and Ruff Documentation, and that `research.md` includes corresponding entries, cannot be verified because no such files or excerpts were provided. The required documentation updates are missing from the evidence.
- **T030** — declared artifact(s) missing/empty/invalid: data/results/execution_outcomes.csv
- **T033** — The provided `stats.py` only shows a partial LMM implementation with a random intercept for `problem_id`, not for problem difficulty based on canonical pass rates, and it lacks the required edge‑case exclusion logic and logging to `data/results/excluded_problems.csv`. The `excluded_problems.csv` file is missing, and there is no evidence that the fallback is documented in `research.md`.
