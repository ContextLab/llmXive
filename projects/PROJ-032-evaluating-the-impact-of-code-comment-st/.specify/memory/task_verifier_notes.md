# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — declared artifact(s) missing/empty/invalid: src/code/extract.py
- **T015b** — No code artifact showing a modified `clone_batch` function with retry and skip logic (or corresponding tests/logs) was provided. Without the actual implementation or evidence that errors are logged and processing continues, the requirement cannot be confirmed. The next implementer must add and expose the updated `clone_batch` code (and optionally tests) demonstrating the retry‑on‑failure behavior.
- **T015c** — No code artifact for `clone_batch` was provided, and there is no evidence that a check for empty git history was added or that exclusions are logged. The required implementation and logging are missing.
- **T016** — No `logs/acquisition_stats.json` file or its contents were provided; thus there is no evidence that the required JSON logging of success rate, excluded repos count, and total valid clones was added. The implementer must create this file with the specified statistics.
- **T021** — declared artifact(s) missing/empty/invalid: src/code/extract.py, data/processed/comments.json
- **T027** — The required output file `data/processed/metrics.csv` does not exist, so the aggregation of the specified metrics cannot be verified. The task’s core deliverable is missing.
- **T032b** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.json
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/analysis_results.json
- **T034** — No updated `analysis.py` file or diff was provided showing the replacement of causal verbs with correlational verbs and the addition of a disclaimer to every report section. Without the actual code changes, we cannot confirm the required modifications were made. The implementer must supply the modified `analysis.py` (or a patch) demonstrating the verb substitution and disclaimer insertion.
