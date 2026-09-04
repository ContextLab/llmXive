# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory being present, nor any script or log showing that the implementer checked for its existence and created it if missing. The required artifact (the `code/` folder) is absent, so the task is not satisfied.
- **T001b** — No evidence was provided that a `tests/` directory was created or that its existence was verified; the implementer did not supply any file listings, scripts, or output confirming the directory’s presence. The required artifact is missing.
- **T001c** — No files or code were provided showing that the `data/raw/`, `data/processed/`, and `data/figures/` directories were actually created or verified; the claim is unsubstantiated. The required artifact (the three directories) is missing from the evidence.
- **T001d** — No code, script, or other artifact was provided that checks for the existence of `code/`, `tests/`, `data/raw/`, `data/processed/`, and `data/figures/` and raises a `FileNotFoundError` if any are missing. Without such an implementation, the task’s requirement is not satisfied.
