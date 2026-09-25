# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `data/raw` directory (or any files within it) was provided; the implementer did not supply the required artifact, so the task of creating the data directory is not satisfied.
- **T001b** — No artifact showing a `data/processed` directory was provided; there is no file‑system listing, code snippet, or commit evidence that the directory exists or contains any files. The claim lacks concrete proof that the required directory was actually created.
- **T001c** — No evidence of a `data/assets` directory is provided; the artifact is missing or not shown, so the requirement to create the data directory is not satisfied.
- **T002** — No evidence of the required `code`, `artifacts`, or `tests` directories (or their contents) is provided; without confirming their existence and non‑emptiness, the task requirement is not satisfied.
- **T004** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black/Ruff settings, or a pre‑commit hook) are present, nor any evidence that these tools have been set up in the repository or CI pipeline. The required artifacts to satisfy task T004 are missing.
- **T009** — No code, configuration, or generated files were presented that create a logging system writing structured logs to `artifacts/logs/` or a `artifacts/metrics.json` file. The required artifacts are missing, so the task is not satisfied.
