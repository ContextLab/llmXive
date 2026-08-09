# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The `survey_2023.json` only lists tags without the required category mapping, and `reference_calendar.json` is an empty array instead of containing parsed release‑log events with dates. No evidence of actually fetching the HuggingFace dataset or processing release logs is present. The task’s core requirements are therefore unmet.
- **T015** — The `code/analysis/mapping.py` file is present and contains substantial mapping logic, but the required input file `data/processed/external_metrics.json` is missing, so the module cannot actually perform the mapping as specified. Without this data the implementation cannot be verified as functional.
- **T018** — The required output file `data/processed/trend_results.json` does not exist on disk, so the aggregation and finalization step cannot be verified as completed. The missing artifact must be created and populated with the expected trend analysis results.
