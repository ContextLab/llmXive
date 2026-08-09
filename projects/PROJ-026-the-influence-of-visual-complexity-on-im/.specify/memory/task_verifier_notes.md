# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T033a** — No `research.md` file or excerpt was provided, and there is no evidence that the methodological shift from ANOVA to a permutation test has been documented, justified, or cited as required. The implementer must supply a non‑empty `research.md` containing the explanation and citation.
- **T027a** — declared artifact(s) missing/empty/invalid: data/processed/counterbalance_assignment.csv
- **T027b** — No evidence of a `logs/counterbalance_strategy.log` file was provided; the claim lacks any artifact showing the log’s existence, content, or the specific counterbalancing strategy recorded. The required log file must be present and contain the strategy details for the task to be considered complete.
- **T017** — The `code/stimuli/process.py` script is present and implements the required processing and CSV schema, but the expected output file `data/processed/complexity_scores.csv` does not exist, so the task’s required artifact is missing.
- **T018** — No code, notebook, script, or output file was provided that actually computes visual‑complexity scores and applies `pandas.qcut` to assign Low/Medium/High categories. Without the required artifact (e.g., a Python module or CSV showing the categorized images), the task’s requirement is not satisfied.
- **T024** — No code, script, or data file implementing the exclusion of participants with fewer than 10 valid trials and flagging their D‑score as `NaN` was provided. The required artifact is missing, so the task is not satisfied.
- **T026** — The required output file `data/processed/aggregated_d_scores.csv` does not exist, and the provided `code/data/process.py` is truncated with no visible logic that writes the aggregated DataFrame to that CSV (nor a complete implementation of the aggregation function). The task’s core deliverable is therefore missing.
- **T036** — declared artifact(s) missing/empty/invalid: data/results/permutation_results.json, data/results/sensitivity_results.json
- **T043a** — declared artifact(s) missing/empty/invalid: github/workflows/analysis.yml
