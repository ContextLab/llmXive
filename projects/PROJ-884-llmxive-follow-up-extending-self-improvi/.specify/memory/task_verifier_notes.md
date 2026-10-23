# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T001** — The pytest run fails (exit 4) because `pyproject.toml` is invalid, so the required tests never pass. Moreover, the generated puzzle JSON lacks the required `verifier_output` field defined in `contracts/dataset.schema.yaml`, causing schema validation to fail. The benchmark test also does not explicitly assert the < 100 ms limit. These issues must be fixed for the task to be considered complete.
- **T002** — The required test suite `code/tests/test_symbolic_planner.py` is missing, so the observable check cannot be performed. Additionally, `code/symbolic/parser.py` calls `raise_parse_failure` without importing or defining it, causing a runtime NameError. Consequently the parser does not correctly emit the required `PARSE_FAILURE` code, and the exclusion log file is absent until a run creates it. These gaps prevent the task from being fully satisfied.
