# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains the required directories, `requirements.txt`, `config.py`, `fetch_data.py`, and the unit‑test file, and `outputs/fetch_log.txt` shows sample IDs, but there is no evidence that `pytest code/tests/test_fetch_data.py -v` was actually executed and passed, nor any artifact proving that the combined fetched species count meets the ≥ 50 requirement.
- **T002** — The provided `code/src/preprocess.py` does not satisfy the task: the pytest suite (`code/tests/test_preprocess.py`) fails (benzoxazinoids mean ≠ 0 after scaling and outlier capping test fails). Additionally, the schema file `contracts/processed_data.schema.yaml` is parsed with `json.load`, causing a JSON‑parse error and skipping validation, which violates the requirement to validate against the schema. The pipeline therefore does not meet the specified behavior or pass its own tests.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
