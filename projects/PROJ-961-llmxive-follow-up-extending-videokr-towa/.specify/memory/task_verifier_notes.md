# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `code/`, `tests/`, or `data/` directories (or any files within them) was provided; the claim lacks any tangible artifact confirming their creation.
- **T001b** — No evidence was provided that the required subdirectories `code/ingest/`, `code/analysis/`, and `code/utils/` actually exist in the repository; the response contains only a textual description of the feature specification without any file listings or directory structures. The implementer must create and show these three non‑empty directories.
- **T001c** — No evidence was provided showing that the `tests/unit/` and `tests/integration/` directories actually exist in the repository; the claim is unsupported and the required subdirectories are not demonstrated.
- **T008a** — No `.gitkeep` file in `data/raw/` was shown or described; the implementer provided no artifact or proof that the file exists, so the required output is missing.
- **T008b** — No evidence of a `.gitkeep` file in the `data/processed/` directory is provided; the implementer did not supply the required artifact, so the task is not verified as completed.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/annotated_videokr.csv
- **T015** — No `annotate_graph.py` file containing a proactive two‑stage sampling implementation is provided, nor any benchmark or test showing the analysis finishes within 6 hours on a 2‑core runner. The claim lacks the required artifact and runtime evidence.
- **T021** — The implementer supplied only a high‑level feature description and user stories; there is no evidence of any changes to `detect_threshold.py`, no code, tests, or output demonstrating handling of small bin sizes. The required artifact (updated script handling small bins) is missing.
- **T022** — The response contains only the task description and no actual artifacts such as the annotated dataset, summary table, statistical test results, or the required plots. Consequently, there is no evidence that the summary table and visualizations were generated, so the requirement is not satisfied.
- **T026** — No comparison table (or any other output) was provided; the response contains only the task description and no concrete artifact such as a CSV/markdown table showing accuracy or other metrics across hop thresholds. The required deliverable is missing.
- **T027** — No overlay plot or any data/analysis artifacts were provided; the claim contains only the task description and specifications, with no figure, code, or results to verify that accuracy curves for different threshold definitions were actually created. The required overlay plot is missing.
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.md
- **T029** — No README or usage instruction files were provided in a `docs/` directory, nor any evidence that documentation was updated; the response only contains a feature specification and no documentation artifacts.
