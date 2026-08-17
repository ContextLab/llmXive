# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw`, `data/distorted`, `data/outputs`, `data/metadata`) being present or populated is provided; the prompt contains no file‑system listing or screenshots confirming their creation. The implementer’s claim cannot be verified without concrete artifacts.
- **T001b** — No evidence was provided showing that the three required directories (`src/generators`, `src/inference`, `src/analysis`) actually exist in the repository; without a directory listing or similar proof, we cannot confirm the task was fulfilled. The implementer must create the directories and supply a view (e.g., `tree` output) confirming their presence.
- **T001c** — The implementer supplied only a feature specification and no file system evidence; there is no indication that `tests/unit` or `tests/integration` directories were created, nor any listing or content showing those folders. The required test directory structure is missing.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or related setup scripts) were provided, nor any evidence that ruff and black have been integrated into the project. The required artifacts are missing, so the task is not satisfied.
- **T005** — No evidence of a `models/` directory is provided; the artifact list is empty, so we cannot confirm that the required cache directory was actually created. The implementer must add the `models/` folder (non‑empty or at least present) to satisfy the task.
- **T007a** — The required file `specs/001-extreme-aspect-ratio-robustness/contracts/dataset.schema.yaml` does not exist on disk, so the schema definition for the synthetic video metadata is missing. The task is therefore not satisfied.
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007c** — The required file `specs/001-extreme-aspect-ratio-robustness/contracts/metric.schema.yaml` is missing from the repository, so no schema definition is provided. Without this artifact the task is not satisfied.
- **T008** — No configuration scripts, Dockerfiles, cgroup/ulimit wrapper code, or documentation were presented to demonstrate that memory and time limits have been set up. The required artifacts for task T008 are missing, so the claim is not substantiated.
- **T012b** — declared artifact(s) missing/empty/invalid: src/generators/fetch_original.py
- **T013** — declared artifact(s) missing/empty/invalid: src/generators/distort_video.py
- **T014** — declared artifact(s) missing/empty/invalid: src/generators/validate_generation.py
- **T015** — No code, configuration, tests, or documentation showing the added error‑handling logic for low‑frame‑rate videos or the detection/flagging of unresolvable 1‑pixel lines was provided. Consequently the required artifact is missing.
