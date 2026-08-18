# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021c** — The repository contains the metric‑calculation functions in `code/validation.py`, but there is no code that writes the results to `data/raw/repo_metrics.json`, and that file is absent from the project. Consequently the required output artifact does not exist.
- **T021b** — The required file `data/raw/repo_selection_rubric.json` is missing, and the checksum entry in `data/checksums.txt` does not reference that JSON (it only contains a hash for `data/llm_config.yaml`). Consequently the task’s core outputs and verification steps are not satisfied.
- **T021d** — declared artifact(s) missing/empty/invalid: data/raw/repo_matching_report.json
- **T021g** — declared artifact(s) missing/empty/invalid: data/raw/repo_covariates.json
- **T021f** — The repository lacks the required `data/raw/doc_quality_scores.json` file, and the shown `code/validation.py` snippet ends abruptly before completing the scoring logic or writing the JSON output. Consequently, the task’s output artifact does not exist, so the implementation does not meet the specification.
