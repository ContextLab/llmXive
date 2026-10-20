# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` exists but contains version ranges (e.g. `astropy>=6.0,<7.0`), not the fully-pinned exact versions the task requires (e.g. `astropy==6.1.0`); it is essentially the example input, not a `pip-compile` output. Additionally, there is no evidence (log, lock output, or CI record) that `pip install -r requirements.txt` was run and succeeded without conflicts.
- **T003** — Requested task execution failed; rerun successfully: scripts/lint.sh exit=1
- **T004** — Requested task execution failed; rerun successfully: code/download_pantheon.py exit=1
