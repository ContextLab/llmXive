# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: outputs/fetch_log.txt exit=-1
- **T002** — The provided `code/src/preprocess.py` does not satisfy the task: the pytest suite (`code/tests/test_preprocess.py`) fails (benzoxazinoids mean ≠ 0 after scaling and outlier capping test fails). Additionally, the schema file `contracts/processed_data.schema.yaml` is parsed with `json.load`, causing a JSON‑parse error and skipping validation, which violates the requirement to validate against the schema. The pipeline therefore does not meet the specified behavior or pass its own tests.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
