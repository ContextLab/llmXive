# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — No `.gitignore` file was presented, and there is no evidence that a file containing the required exclusion patterns (`__pycache__`, `*.pyc`, `.env`, `data/raw/*.csv`) exists. The implementer must provide the actual `.gitignore` with those entries (and ensure the CSV entries are checksummed only) for the task to be considered complete.
- **T007** — declared artifact(s) missing/empty/invalid: conftest.py
- **T020a** — The repository contains `code/analysis.py` with a `validate_data_structure` function, but the required output file `data/processed/structure_config.json` is missing, and the JSON written by the function includes an extra `n_observations` field that does not match the specified schema of only `"type"` and `"n_subjects"`. The task’s output artifact is therefore absent or incorrect.
- **T025** — The provided `tests/contract/test_model_output.py` is truncated and contains a syntax error (unterminated string in the last assert), and it does not actually load or validate against the required `contracts/model_output.schema.yaml` which is missing from the repository. Both the test file and the referenced schema are incomplete, so the task is not satisfied.
