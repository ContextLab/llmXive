# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The JSON file is present and has an `analysis_mode` key, but it lacks the required `power_status` entries (for primary and fallback modes) and does not record the specific under‑power flags (`underpowered_primary` or `underpowered_fallback`) as stipulated. The report must include these fields to satisfy the task.
- **T004** — The `fetch_huggingface_datasets` and `fetch_openneuro_datasets` functions log errors but then re‑raise the exception, causing the pipeline to abort instead of skipping the failed dataset. No surrounding logic is present to catch these errors and continue processing other datasets, so graceful degradation is not implemented.
- **T005c** — Checked the repository root for a `.git` directory or any record of `git init` having been run; none is present among the listed top‑level items (src/, analysis/, data/, utils/). Without a `.git` folder or other proof of initialization, the required Git repository does not exist.
- **T024** — Requested task execution failed; rerun successfully: code/src/data/finalize_aligned.py exit=1
- **T030** — declared artifact(s) missing/empty/invalid: src/analysis/robustness.py
