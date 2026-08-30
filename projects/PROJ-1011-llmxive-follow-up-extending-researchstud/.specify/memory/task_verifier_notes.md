# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — The required test file `tests/unit/test_memory_usage_constraint.py` is missing from the repository, so no test code exists to verify the memory usage constraint. Without this artifact, the task is not satisfied.
- **T019** — The required test file `tests/unit/test_preprocessing_validation.py` does not exist in the repository, so there is no artifact to verify that abstracts are non‑empty. Without this file, the preprocessing validation test cannot be run, meaning the task’s requirement is unmet.
- **T024** — declared artifact(s) missing/empty/invalid: data/results/generated_proposals.jsonl
- **T025** — No code, scripts, logs, or performance measurements were provided to demonstrate that batch processing was added to T021/T022, that memory usage stays ≤ 7 GB, or that the full generation of 100 proposals completes within 4 hours. The claim lacks any concrete artifact (e.g., updated pipeline files, benchmark results, or CI logs) required to verify the requirement.
- **T026** — declared artifact(s) missing/empty/invalid: data/results/generated_proposals.jsonl
- **T029** — declared artifact(s) missing/empty/invalid: tests/unit/test_proposal_generation_logic.py
- **T030a** — The repository contains a partially‑written `code/04_evaluation_recruitment.py` that is truncated and does not include logic to write `ratings_template.csv` or fully implement the metadata‑stripping routine. Moreover, the required output files `data/results/ratings_template.csv` and `data/results/generated_proposals.jsonl` are absent from the project. The task’s core deliverables are therefore missing.
