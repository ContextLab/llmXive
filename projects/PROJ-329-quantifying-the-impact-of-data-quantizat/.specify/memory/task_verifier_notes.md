# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — No code, scripts, or documentation implementing checksumming for the `data/raw/` and `data/processed/` directories was provided. The required data‑hygiene utilities are missing, so the task is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: src/utils.py
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No code, configuration files, tests, or documentation were provided that show error handling for missing or corrupted noise files has been added. The claim lacks any tangible artifact demonstrating the required graceful‑failure behavior, so the task is not satisfied.
- **T009** — No configuration files, scripts, or documentation were provided that set random seeds, define CI resource limits (2 CPU, 7 GB RAM), or contain the calculated batch‑size constraints for a pilot of N = 1200. The required artifacts are missing, so the task is not satisfied.
- **T010** — No calculation, table, or written documentation showing that the batch size N = 1200 fits within the 6‑hour CI time limit and 7 GB RAM constraint is present. The implementer supplied only the task description without any quantitative analysis or evidence, so the required artifact is missing.
- **T011** — The required artifact `tests/unit/test_quantization.py` is missing entirely, so no unit test code exists to verify the 1‑bit and 16‑bit edge cases. Without this file, the task’s deliverable is not present.
- **T012** — The required artifact `tests/integration/test_injection.py` does not exist, so no integration test verifying the SNR range [8, 50] is present. The task’s core deliverable is missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/data_generation.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data_generation.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data_generation.py
