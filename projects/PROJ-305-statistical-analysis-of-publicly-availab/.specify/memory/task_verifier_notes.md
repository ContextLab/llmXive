# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
- **T003** — The provided `src/data/validate.py` does not match the required CLI (`--input` option, single failure exit 1) and the unit‑test suite fails (missing‑column and valid‑run tests raise `SystemExit` 3). Moreover the required fixture `tests/fixtures/malformed_missing_vax_type.csv` is absent. Fix the CLI arguments, unify exit codes, ensure CSV reading works, add the missing fixture, and make all tests pass.
