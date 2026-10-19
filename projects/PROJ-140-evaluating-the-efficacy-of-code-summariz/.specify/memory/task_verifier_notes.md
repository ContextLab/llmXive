# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart file exists (3614 bytes) with correct content — layout, pinned Defects4J v2.0 (matching `data/defects4j_version.txt` containing `2.0`), seed 42, and the run command — but the task's explicit verification step (`python -m code.main --mode sim --help` exiting with status 0) has no execution evidence: no command output, exit code, or run log was supplied, and `code/main.py`'s contents were not shown to confirm it defines a `--mode sim` CLI with a working `--help`. The next implementer should run the command from the project root and capture its exit status/output as evidence.
- **T002** — Requested task execution failed; rerun successfully: code/download/download_defectsj.py exit=1
