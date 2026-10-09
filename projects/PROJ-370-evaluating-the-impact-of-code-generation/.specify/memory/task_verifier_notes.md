# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The only evidence is that `src/utils/logger.py` and `src/utils/timeout_wrapper.py` exist; no code, test results, or logs are provided to show they enforce a 6 h limit, write to `logs/timeout.log`, exit with code 143, or emit valid JSON‑line logs. Without this concrete implementation or test output, the task requirements are not demonstrated.
- **T005** — Requested task execution failed; rerun successfully: src/cli/main.py exit=1
- **T006** — The three contract YAML files exist, and the schema modules import without syntax errors, but the required `BugDetection` dataclass is **not** defined in `src/detection/schema.py` (it is incorrectly placed in `src/extraction/schema.py`). The detection schema currently only defines `LLMCodeDetectionResult`, so the task’s core requirement of providing a `BugDetection` model in the detection package is missing.
- **T007** — Requested task execution failed; rerun successfully: code/src/extraction/fetch_prs.py exit=1
- **T008** — Requested task execution failed; rerun successfully: src/extraction/preprocess_and_ground_truth.py exit=1
