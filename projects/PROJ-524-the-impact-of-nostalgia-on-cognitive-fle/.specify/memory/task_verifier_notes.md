# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `data/raw/` directory is provided; the claim lacks any visible artifact (e.g., a directory listing or placeholder file) confirming that the required folder exists. The implementer must create the directory in the repository and show its presence (e.g., via a file tree screenshot or a placeholder file inside).
- **T001b** — No evidence was provided that a `data/processed/` directory actually exists in the repository, nor any listing showing it was created or contains files. The implementer must add the required directory (and optionally a placeholder file) to satisfy task T001b.
- **T001c** — No evidence was provided showing that a `data/results/` directory actually exists in the repository, nor any contents within it. The implementer’s claim cannot be verified without a concrete artifact (e.g., a directory listing or a file inside the folder). The missing directory must be created and confirmed.
- **T001e** — No evidence of a `data/stimuli/` directory (or its contents) was provided; the claim is unsupported and the required artifact is missing.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or scripts invoking ruff/black) are present in the provided evidence, nor any documentation showing they have been set up. Without these artifacts the requirement to configure ruff and black is not satisfied.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T013b** — No code, configuration file, or log output was provided that checks for an ‘MMSE’ column, sets a `has_mmse` flag, or emits the `ERR_MMSE_MISSING` warning. The required implementation artifact is missing, so the task is not satisfied.
- **T014a** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
