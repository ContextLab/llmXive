# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked the `code/src/audit/` directory (modules present) and the `quickstart.md` which contains the exact command `python -m code.src.audit.run_audit data/input/urls.csv output/`. However, there is no evidence that running `python -m code.src.audit.run_audit --help` actually exits with status 0 (no command‑line output or exit‑code log is provided). Add a recorded execution (e.g., terminal capture showing exit code 0) to satisfy the verification requirement.
- **T004** — Requested task execution failed; rerun successfully: code/src/audit/monte_carlo_validation.py exit=1
