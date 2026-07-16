# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file contents were provided showing that `src/`, `tests/`, `data/`, and `specs/001-gene-regulation/` actually exist in the repository. Without concrete evidence of these folders (and any files within them), the claim that the required project structure has been created cannot be verified. The implementer must add the missing directory structure (and optionally placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a `requirements-dev.txt` including these tools) were provided, nor any documentation or scripts showing they have been set up and integrated into the project. The required artifacts are missing.
- **T004** — No evidence of the required directories (`data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`) is provided; the claim lacks any artifact listing or screenshots confirming their existence or contents.
- **T008** — No code, configuration, or documentation was provided that creates or demonstrates logging of experiment run IDs, timestamps, and parameter hashes. The evidence consists only of a high‑level feature specification unrelated to state‑tracking, so the required artifact is missing.
- **T009a** — declared artifact(s) missing/empty/invalid: data/gold_standard/human_annotations.json, schema.yaml
- **T010** — The required file `specs/001-gene-regulation/contracts/axis.schema.yaml` (or `schema.yaml`) does not exist, so no JSON schema for `CharacterAxis` (Coarse/Fine) is provided. The task’s primary artifact is missing.
- **T011** — declared artifact(s) missing/empty/invalid: src/services/axis_generator.py, data/derived/axes.jsonl, src/cli/run_experiment.py
- **T011a** — declared artifact(s) missing/empty/invalid: src/cli/axis_input.py
- **T012** — declared artifact(s) missing/empty/invalid: src/services/axis_generator.py
- **T012a** — declared artifact(s) missing/empty/invalid: src/cli/axis_input.py
- **T013** — declared artifact(s) missing/empty/invalid: data/derived/axes.jsonl
