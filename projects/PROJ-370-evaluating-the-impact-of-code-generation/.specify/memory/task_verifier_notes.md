# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The claim only provides a feature specification and no visible evidence that the required directories (`src/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`) actually exist in the repository. Without directory listings or files confirming their creation, the task is not satisfied. The implementer must create the specified folders and provide proof (e.g., a directory tree listing).
- **T004** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or similar) were presented, nor any evidence (scripts, documentation, CI integration) showing that ruff and black have been configured for the project. Consequently the required artifact is missing.
- **T006** — The required file `src/extraction/schema.py` does not exist, so the data classes PullRequest, BugDetection, and AlignmentResult are not defined. The implementer must create this file and implement the specified data classes.
- **T007** — The required file `src/detection/schema.py` does not exist, so no data class (LLMCodeDetectionResult) is defined. The implementer must add the missing file with the appropriate data class implementation.
- **T008** — The required file `src/inference/schema.py` does not exist, so the data classes `InferenceRequest` and `InferenceResponse` are not defined. The implementer must add this file with the appropriate data class definitions.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/timeout_wrapper.py
- **T010** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T011** — The claim mentions creating `contracts/` YAML schemas, but no YAML files (e.g., `contracts/pr_data.yaml`, `contracts/bug_detection.yaml`, `contracts/alignment_result.yaml`) are present or referenced in the provided evidence. Without the actual schema files, we cannot verify that the required artifacts exist or contain the correct structure. The implementer must add the YAML schema files in the `contracts/` directory.
- **T018** — declared artifact(s) missing/empty/invalid: src/detection/detect_llm_code.py, data/derived/llm_detections.json
- **T019** — declared artifact(s) missing/empty/invalid: src/inference/load_model.py
- **T019b** — declared artifact(s) missing/empty/invalid: src/utils/memory_watchdog.py
- **T020** — declared artifact(s) missing/empty/invalid: src/inference/prompt_templates.py
- **T021** — declared artifact(s) missing/empty/invalid: src/analysis/split_dataset.py
- **T022** — declared artifact(s) missing/empty/invalid: src/inference/run_inference.py
- **T023** — declared artifact(s) missing/empty/invalid: src/inference/run_inference.py
- **T024** — declared artifact(s) missing/empty/invalid: data/derived/llm_detections.json
