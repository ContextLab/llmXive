# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure is shown or listed in the provided evidence; the implementer did not supply any proof that the required folders (`src/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`) actually exist. The task remains undone.
- **T004** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or ruff section in `pyproject.toml`, or corresponding CI scripts) were presented. Without these artifacts, the requirement to configure ruff and black cannot be confirmed as satisfied. The implementer must add the actual configuration files and, optionally, demonstrate they are active (e.g., via a lint/format run).
- **T006** — declared artifact(s) missing/empty/invalid: src/extraction/schema.py
- **T007** — declared artifact(s) missing/empty/invalid: src/detection/schema.py
- **T008** — declared artifact(s) missing/empty/invalid: src/inference/schema.py
- **T008b** — No evidence was provided that a `src/utils/` directory exists in the repository; the claim is unsupported and the required artifact is missing.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/timeout_wrapper.py
- **T009c** — declared artifact(s) missing/empty/invalid: src/cli/main.py
- **T009b** — The required source files `src/utils/timeout_wrapper.py` and `src/cli/main.py` are absent, so no integration, runtime tracking, or graceful skipping logic exists. The task’s core deliverable cannot be verified.
- **T010** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T011** — No `contracts/` directory or YAML schema files for PR data, BugDetection, or AlignmentResult are present in the provided evidence; thus the required artifacts are missing. The implementer must add the `contracts/` folder containing the three YAML schema definitions.
- **T014b** — declared artifact(s) missing/empty/invalid: src/extraction/fetch_human_comments.py, data/annotations/raw_comments.json
- **T014c** — declared artifact(s) missing/empty/invalid: src/extraction/filter_human_confirmations.py, data/annotations/raw_comments.json, data/derived/human_confirmations.json
- **T015** — The repository contains a `src/extraction/preprocess.py` file, but the shown code does not include any logic that writes raw JSON files to `data/raw/` nor generates a `data/raw/checksums.json`. Moreover, the required `data/raw/checksums.json` file is absent from the project. The task’s core requirement—saving raw JSON with SHA‑256 checksums—is therefore not fulfilled.
- **T016** — No code, tests, or documentation were provided showing that validation logic for `linked_issue_ids` was added, nor any evidence that the IDs are checked to be labeled “reported” and not ground‑truth. The required implementation artifact is missing.
- **T017** — declared artifact(s) missing/empty/invalid: src/extraction/generate_ground_truth.py, data/derived/human_baseline.json, data/derived/human_confirmations.json
- **T018** — declared artifact(s) missing/empty/invalid: src/detection/detect_llm_code.py, data/derived/llm_detections.json
