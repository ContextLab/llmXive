# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The required top‑level directory `projects/001-crack-propagation-ml/` does not exist; the existing `code/`, `data/`, `tests/`, `specs/`, and `contracts/` folders are at the repository root, not under the specified project path, so the mandated layout is missing.
- **T001b** — The required `__init__.py` files are present, but there is no documented evidence (e.g., command output or test log) showing that `python -c "import code"` runs without an `ImportError`. Provide execution proof to satisfy the verification step.
- **T002** — The provided `requirements.txt` and `pyproject.toml` list dependencies with minimum version specifiers (`>=`) rather than exact, pinned versions, and there is no evidence that `pip install -r requirements.txt` succeeded or that `python -m build` produced a valid build. The task’s requirement for a fully pinned dependency list and successful build verification is therefore unmet.
- **T003** — Requested task execution failed; rerun successfully: scripts/run_lint.sh exit=2
