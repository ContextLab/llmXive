# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `requirements.txt` does include the nine required pinned packages, but it also contains a stray line (`pi`), duplicate/unpinned entries (e.g., `networkx` without version), and a long list of unrelated packages, so it does not match the task’s specification of a clean requirements file containing only the specified pinned versions.
- **T003** — The repository contains a valid `pyproject.toml` with Black configuration, but there is no `.flake8` file present, and no execution evidence (e.g., command output or logs) showing that `black --check .` and `flake8 code/` succeed. Both the missing configuration file and lack of verification results must be provided.
