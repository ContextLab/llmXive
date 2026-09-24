# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: src/utils/timeout_utils.py
- **T010** — No evidence of the four required prompt files (`zero_shot_basic.txt`, `zero_shot_style.txt`, `few_shot_basic.txt`, `few_shot_style.txt`) was provided; the claim lacks the actual files or their contents, so the task is not satisfied. The implementer must add these files in `data/prompts/` with complete, non‑placeholder prompt text as specified.
- **T022** — No script, configuration, or log files were provided that demonstrate seeds being pinned or the required logging of prompt text, model version, and seed for each request. Without concrete artifacts showing this deterministic‑execution functionality, the task’s requirement is not satisfied.
- **T023** — No code, script, or directory structure was provided showing that translation outputs are being saved under `data/evaluation/raw_translations/` with sub‑folders for each prompt condition. Without such artifacts, we cannot confirm the required storage implementation exists.
- **T024** — No code, script, or log modifications were provided to demonstrate that the system now records a “failed translation” entry when the LLM returns non‑code text. Without an artifact showing the added logging logic (e.g., updated inference or post‑processing module and example log output), the requirement cannot be confirmed.
- **T025c** — declared artifact(s) missing/empty/invalid: src/evaluation/generate_metadata_log.py, data/evaluation/metadata_log.csv
- **T025** — The required artifact `tests/contract/test_test_translation.py` does not exist in the repository, so the contract test for test translation is missing. The task cannot be considered completed until this file is created with appropriate test content.
- **T029** — declared artifact(s) missing/empty/invalid: src/evaluation/compute_quality.py
- **T030** — declared artifact(s) missing/empty/invalid: src/evaluation/statistical_analysis.py
- **T031** — declared artifact(s) missing/empty/invalid: data/evaluation/statistical_summary.csv
- **T032** — The required artifact `src/utils/update_state.py` does not exist in the repository, so the integration cannot be verified. The missing file must be added with the appropriate logic to update the system state after evaluation completes.
