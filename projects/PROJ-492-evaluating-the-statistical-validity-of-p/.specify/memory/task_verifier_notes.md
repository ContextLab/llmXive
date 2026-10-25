# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains the consolidated `code/src/audit/` package, the duplicate‑check script reports no PT### duplicates, and `quickstart.md` documents the required command. However, there is no provided execution evidence that `python -m code.src.audit.run_audit --help` actually runs and exits with status 0, which is a mandatory verification step. Adding a logged run (or test) of that command with a successful exit code is needed to complete the task.
- **T017** — Requested task execution failed; rerun successfully: code/src/audit/curate_corpus.py exit=1
