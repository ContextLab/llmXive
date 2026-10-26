# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories and `data/dir_structure.txt` are present and correctly list the nine paths, but the CI verification step fails – the integration test `tests/integration/test_dir_structure.py` crashes with an import error (`AttributeError: partially initialized module 'subprocess' has no attribute 'PIPE'`), so the manifest is never asserted to contain the expected entries. The task’s verification requirement is therefore not satisfied.
- **T006** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T007** — Requested task execution failed; rerun successfully: code/main.py exit=1
