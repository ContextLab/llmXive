# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories all exist, and `quickstart.md` documents the runnable command, but `logs/structure.txt` does not list the expected directories (unit test `test_structure_contains_some_required_dirs` fails), so the verification step is not satisfied. The structure snapshot must be regenerated to include the required paths (or depth increased) so the grep‑count check passes.
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
