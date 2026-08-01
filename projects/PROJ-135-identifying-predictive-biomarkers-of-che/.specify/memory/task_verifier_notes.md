# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: src/feasibility.py, data/feasibility_gate.json
- **T010** — The `tests/contract/test_data_schema.py` file is present but is truncated (ends with an incomplete `except` block) and therefore contains a syntax error. Moreover, the required `dataset.schema.yaml` file does not exist at the referenced path, so the test cannot actually load or validate any schema against raw data. Both the missing schema and the broken test mean the contract test does not fulfill the requirement.
- **T011** — declared artifact(s) missing/empty/invalid: tests/integration/test_acquisition.py, data/feasibility_gate.json
- **T012** — declared artifact(s) missing/empty/invalid: src/data_acquisition.py
- **T012c** — No code, script, log, or test output is provided that shows a SHA256 checksum being calculated immediately after each file is downloaded into `data/raw/` and appended to an in‑memory list. The required artifact (implementation of per‑file checksum logic) is missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/data_acquisition.py
