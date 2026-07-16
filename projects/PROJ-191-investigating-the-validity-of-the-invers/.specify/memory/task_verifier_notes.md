# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or listing of the required `projects/PROJ-191-investigating-the-validity-of-the-invers/` sub‑folders is present in the provided evidence; without concrete artifacts we cannot confirm the tree was created in a single atomic operation. The implementer must supply a visible file‑system snapshot (e.g., `tree` output or a zip archive) showing all required sub‑directories.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml` with black settings) are present in the provided evidence, so the requirement to configure ruff and black is not demonstrated. The implementer must add the appropriate configuration artifacts.
- **T005** — declared artifact(s) missing/empty/invalid: code/config.py
- **T007** — No directory structure or script implementing robust `mkdir -p` logic was provided; there is no evidence that `data/raw/`, `data/processed/`, and `data/results/` actually exist or that code creates them. The implementer must supply the created directories (or a script that creates them) as proof.
