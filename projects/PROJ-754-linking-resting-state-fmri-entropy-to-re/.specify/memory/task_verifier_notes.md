# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required source and test directories exist with Python files, and `quickstart.md` lists end‑to‑end commands, but the validation step fails: the recorded pytest run (`code/.tasks/T001.code_tests_unit_test_directory_structure.py.log`) shows `test_required_directories_and_modules` exiting with failure because the expected path `code/code/src/data` is missing. Consequently `pytest code/tests/` does not pass, violating the task’s validation requirement. The implementer must fix the directory layout (or the test) so that the pytest suite succeeds.
- **T002** — Requested task execution failed; rerun successfully: code/src/data/download_hcp.py exit=1
