# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — The evidence contains no linting or formatting configuration files (e.g., `.ruff.toml`, `pyproject.toml` with Black settings, or a pre‑commit hook) and no scripts showing ruff/black integration. Without these artifacts the requirement to “configure linting (ruff) and formatting (black) tools” is not satisfied. Adding the appropriate config files and confirming they run would resolve the issue.
- **T004** — The evidence contains no `checksum.py` script (or any related files) in the project root or subdirectories, nor any documentation or execution logs showing that such a script was created and functions for artifact versioning. Without the required script, the task is not satisfied.
- **T014c** — Requested task execution failed; rerun successfully: code/data/generate_pilot_sample.py exit=1
