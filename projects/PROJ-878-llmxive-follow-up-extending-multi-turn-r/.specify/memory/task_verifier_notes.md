# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or screenshots were provided, so there is no evidence that the required folders (`data/raw/`, `data/processed/`, `code/`, `code/utils/`, `tests/`, `results/paper_figures/`) actually exist in the repository. The implementer must create these directories and show their presence (e.g., via a file tree or `ls` output).
- **T002** — No evidence was provided showing that `__init__.py` files exist in the `code/`, `code/utils/`, or `tests/` directories; the claim lacks the required artifacts. The implementer must add these three files (non‑empty) to satisfy the task.
- **T004** — No linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or related setup scripts) were presented, nor any evidence that ruff and black have been integrated into the project’s workflow. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- **T008** — No configuration file, script, or documentation defining the required environment variables (e.g., `RANDOM_SEED`, `MODEL_PATH`, etc.) is present. The claim provides no artifact that sets or documents these variables, so the task’s core deliverable is missing.
- **T013** — The submission contains only a high‑level feature description and user stories; there is no code, script, or data implementing the required stratified orthogonalization with a rejection‑sampling loop, nor any log or output showing that the |r| < 0.2 constraint was enforced or that a final correlation coefficient was verified and recorded. The necessary artifact is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/validation_metrics.json
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/logical_puzzles.jsonl
- **T017** — declared artifact(s) missing/empty/invalid: data/raw/logical_puzzles.jsonl, data/checksums.txt
