# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T046** — The required artifact `docs/reports/final_report.md` is absent, so the report was never generated. The provided `report_generator.py` script alone does not satisfy the task; the expected markdown output is missing.
- **T047** — No evidence was provided that any files under `results/*.json`, `data/processed/*.json`, or `docs/reports/*.png` actually exist, are non‑empty, or conform to the required schema, so the artifact validation task cannot be considered fulfilled.
- **T048** — No artifact (e.g., test script, logs, or report) showing the pipeline run under simulated network failures or RDKit parsing errors is present; without such evidence we cannot confirm that the system fails loudly as required. The implementer must provide the actual stress‑test execution results or a reproducible script that demonstrates the expected failure behavior.
- **T049** — No artifact (analysis report, calculations, or documentation) was provided that examines the T028 output, confirms statistical power > 0.8, or discusses limitations. The required statistical power review is therefore missing.
