# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `src/`, `tests/`, `data/`, or `specs/` directories is provided; the implementer did not supply any file listings, screenshots, or other artifacts confirming their creation. The task remains undone until those directories are shown to exist and contain appropriate (non‑empty) project files.
- **T001b** — No evidence was provided that the `data/raw`, `data/processed`, and `data/interim` directories actually exist in the repository; the implementer’s claim is not backed by any visible file‑system artifact. The required subdirectories must be created and shown (e.g., via a directory listing or commit diff).
- **T001c** — No evidence of the required `src/data`, `src/features`, `src/models`, or `src/utils` directories is present in the provided artifacts; the implementer did not supply any file listings, screenshots, or code confirming their creation. The task therefore remains unfinished.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T008** — declared artifact(s) missing/empty/invalid: ci.yml
- **T010** — The required artifact `tests/unit/test_preprocess.py` does not exist, so no unit test verifying ≥90% attenuation of the notch filter at 50/60 Hz is present. The task remains undone.
- **T012** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T014** — The repository contains a `src/data/preprocess.py` file, but the shown content is truncated and does not demonstrate the required segmentation logic or the code that writes the centered 60‑second transition windows to `data/processed/centered_transition_windows.parquet`. Moreover, the expected parquet file is absent from the project. Both the implementation and the required output artifact are missing.
- **T014b** — The required output file `data/processed/pre_transition_windows.parquet` does not exist, and the provided `src/data/preprocess.py` is truncated and shows no implementation of the 60‑second pre‑transition window extraction or saving to Parquet. Consequently, the task’s core requirement is unmet.
- **T015** — declared artifact(s) missing/empty/invalid: src/data/loader.py
