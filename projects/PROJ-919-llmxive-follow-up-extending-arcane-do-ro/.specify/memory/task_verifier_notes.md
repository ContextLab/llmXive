# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/`, `tests/`, `data/`, `specs/001-gene-regulation/`) is provided; the claim lacks any file or folder listings to confirm the project structure exists. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present in the provided evidence, nor any documentation showing that ruff and black have been set up for the project. The required artifact—working configuration for both tools—is missing.
- **T004** — No directory listings or file contents were provided, so we cannot verify that `data/raw/`, `data/derived/`, `data/gold_standard/`, and `artifacts/` actually exist or contain any data. The implementer must add evidence (e.g., a directory tree screenshot or a manifest file) showing these folders are present and non‑empty.
- **T009b** — The required file `specs/001-gene-regulation/contracts/calibration.schema.yaml` does not exist (the only listed artifact is a missing `schema.yaml`). Consequently, no schema with the specified fields (character, scenario, ground_truth_score, ground_truth_phase) is provided, so the task is not satisfied.
- **T009c** — declared artifact(s) missing/empty/invalid: data/gold_standard/human_annotations.json, src/scripts/generate_gold_standard.py, schema.yaml
- **T009a** — declared artifact(s) missing/empty/invalid: data/gold_standard/human_annotations.json
- **T010a** — The required file `specs/001-gene-regulation/contracts/axis.schema.yaml` (or `schema.yaml`) is missing, so no JSON schema for `CharacterAxis.Coarse` is present. Without the artifact, the task is not satisfied.
- **T010b** — The required file `specs/001-gene-regulation/contracts/axis.schema.yaml` (or any `schema.yaml` containing the JSON schema for `CharacterAxis.Fine`) is missing from the repository, so no schema was provided. Without the artifact, the task is not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/derived/axes.jsonl
- **T020** — declared artifact(s) missing/empty/invalid: data/derived/probes.jsonl
