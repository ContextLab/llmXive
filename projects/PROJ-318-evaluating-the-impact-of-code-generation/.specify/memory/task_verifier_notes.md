# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — `code/config.py` defines `SEED` and `MAX_METHODS` but does **not** contain the required `TEMPERATURE = 0.2` constant. Consequently the file does not fully meet the specification, even though `code/utils/seed_manager.py` correctly seeds the RNGs. Adding the missing `TEMPERATURE` definition will satisfy the task.
- **T004** — Requested task execution failed; rerun successfully: code/utils/repo_fetcher.py exit=-1 (TIMEOUT)
