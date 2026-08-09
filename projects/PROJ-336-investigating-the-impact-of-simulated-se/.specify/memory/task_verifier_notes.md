# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/`, `tests/`, `data/`, `results/`) is presented; the implementer did not supply a directory listing or any files showing that the project structure has been created.
- **T004** — declared artifact(s) missing/empty/invalid: src/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/atlas.py
- **T006** — The required file `src/data/quality_check.py` is missing entirely, so no code, exclusion manifest, logging, or error‑handling exists to meet the specification. The task cannot be considered done until this file is created with the described functionality.
- **T007** — No `main.py` file or any code implementing the required orchestration, checkpointing, and resumption logic was provided; the evidence section contains no artifacts to verify. The task therefore remains unfulfilled.
- **T008** — No evidence of a modified `main.py` implementing disk‑quota enforcement, compression of intermediate files, or checkpointing is provided; the required artifact is missing, so the task cannot be confirmed as completed.
- **T010** — The required file `tests/unit/test_quality_check.py` does not exist in the repository, so no unit test for FD calculation is present to verify the > 0.5 mm threshold logic. The task’s artifact is missing.
- **T011** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T014a** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T014b** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T015** — No logging code, configuration, or generated log files were presented; the claim that logging for download statistics, exclusion counts, and preprocessing times was added cannot be verified from the provided evidence. The required artifact (implemented logging and its output) is missing.
