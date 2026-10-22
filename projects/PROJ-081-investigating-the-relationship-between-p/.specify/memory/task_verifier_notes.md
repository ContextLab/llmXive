# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `load_and_preprocess` implementation concatenates, renames, filters, caps outliers, validates, writes the parquet file and log, and creates an `absence_indicator` column, so the required files exist and most steps work. However, step 3 of the specification is not fulfilled: metabolite classes documented as biologically absent are filled with zeros **before** StandardScaler is applied, so after Z‑scoring they are no longer zero. The task required inserting a zero **after** standardisation, which the current code does not do. Consequently the pipeline does not meet the full requirement.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
