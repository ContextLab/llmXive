# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T040a** — No `research.md` file in `specs/353-loss-functions-small-world/` is presented, and no content showing the hypothesis (InfoNCE vs CE) or the statistical approach (Tobit/Cox) is provided. The required artifact is missing.
- **T005b** — No `data-model.md` file or its contents were provided; without the markdown document containing the required schema and JSON Schema Draft 7 examples, the task’s deliverable cannot be confirmed as completed. The implementer must supply a non‑empty `data-model.md` that defines the entities (SyntheticGraph, TrainingRun, AnalysisResult) as specified.
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T033** — The provided `code/analyze.py` is truncated (ends mid‑line) and does not contain logic to write the aggregated scalar fields to `data/processed/convergence_logs.csv`. Moreover, the required CSV file is missing from the repository. Consequently the aggregation task is not fully implemented.
- **T034** — No code, module, or script implementing the Tobit regression (using statsmodels or a custom fallback) is present in the provided evidence. The required artifact—a functional Tobit implementation handling censored data with the specified formula—is missing, so the task is not satisfied.
- **T035** — No code, script, or notebook implementing the Cox Proportional Hazards model with `lifelines.CoxPHFitter` is present, nor is there evidence that the `convergence_status` column was renamed to `event` and used in a `fit()` call. The required artifact (the Cox analysis implementation) is missing.
- **T036** — No evidence of the required `data/analysis_results.json` (or any other artifact containing the extracted Tobit and Cox interaction‑term p‑values) was provided. The task demands the specific p‑values to be extracted and saved, which is not demonstrated. The implementer must produce the JSON file with `tobit_interaction_p_value` and `cox_interaction_p_value` (and the `is_significant` flag).
- **T037** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T038** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T039** — declared artifact(s) missing/empty/invalid: data/report.md, data/analysis_results.json
