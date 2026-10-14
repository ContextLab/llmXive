# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The root `src/` and `tests/` contain an `__init__.py`, but the required empty `__init__.py` files are missing from each sub‑package (e.g., `src/data/__init__.py`, `src/models/__init__.py`, `tests/unit/__init__.py`, etc.). Additionally, the `state` directory specified in the task is not present. These omissions mean the project structure does not fully satisfy T001.
- **T003** — The evidence contains no linting or formatting configuration files (e.g., a `pyproject.toml` or `.ruff.toml` specifying Black and Ruff settings, nor a pre‑commit hook), so the requirement to configure Ruff and Black is not demonstrated. Adding the appropriate configuration files and confirming they are present and non‑empty is needed.
- **T005-exec** — Requested task execution failed; rerun successfully: src/scripts/run_validate_citations.py exit=1
- **T006** — the task writes platform-owned path(s) inside the project: `state/projects/...yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
