# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file manifests were provided showing that `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` contains the required sub‑folders (`data/`, `models/`, `experiments/`, `analysis/`, `tests/`). Without concrete evidence of these non‑empty directories, the task requirement is not satisfied.
- **T002** — No evidence of any `__init__.py` files was presented for the directories under `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`. Without visible files, we cannot confirm that the required initialization modules were created. The implementer must add and show the `__init__.py` files in each new directory.
- **T003** — The required file `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt` does not exist, so the project has not been initialized at the specified location. The existing `code/requirements.txt` contains the needed packages, but it is in the wrong directory. The missing file must be created (or moved) at the exact path with the listed dependencies.
- **T004** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The provided material contains only the high‑level feature specification and user stories; there is no code, diff, or file showing a modified `BatchExecutor` with global scheduling logic, nor any tests or documentation proving a 72‑hour wall‑clock limit is enforced. Consequently the required artifact is missing.
- **T015** — The repository contains a partially‑implemented `loader.py` (the `generate_validation_report` function is cut off) and the required `data/validation_report.json` file does not exist. Consequently the validation logic is not fully operational and the deliverable report is missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/intermediate/baseline_run.jsonl
- **T020** — The required `failure_classifier.py` file in `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/analysis/` is not present in the provided evidence, and no code or description of its implementation was supplied. Consequently, the task of detecting “missing context” vs “reasoning error” via sandbox log parsing has not been demonstrated. The implementer must add the file with the specified regex‑based logic.
- **T028** — declared artifact(s) missing/empty/invalid: data/intermediate/hf_run_1b.jsonl
- **T029** — No `context_processors.py` file or code changes were presented showing the required fallback logic, nor any logging statements indicating the edge‑case handling. The artifact needed to verify the implementation is missing.
- **T030** — declared artifact(s) missing/empty/invalid: code/tests/unit/test_glm_analyzer.py
- **T031** — declared artifact(s) missing/empty/invalid: data/intermediate/hf_run_7b.jsonl
- **T032** — declared artifact(s) missing/empty/invalid: data/results.csv
- **T033** — No `glm_analyzer.py` file was presented in the provided evidence, nor any code snippet showing a GLMM or Firth’s penalized likelihood GLM with a binomial link that tests the interaction between “context strategy” and “model size”. The required artifact is missing, so the task is not satisfied.
- **T034** — declared artifact(s) missing/empty/invalid: data/analysis/post_hoc_results.json
- **T035** — The claim provides no evidence that `docs/quickstart.md` and `docs/data-model.md` actually exist or contain updated content; no files or excerpts are shown. Without these documentation artifacts, the requirement cannot be confirmed as satisfied.
- **T036** — No `context_processors.py` file or diff showing cleanup/refactoring was provided; without the actual code artifact we cannot confirm that any code cleanup was performed. The claim lacks the required evidence.
- **T037** — No evidence of a modified `batch_executor.py` or any performance tuning results is provided; the required artifact (the fine‑tuned code and validation that it keeps the total wall‑clock time within the 72‑hour budget) is missing.
