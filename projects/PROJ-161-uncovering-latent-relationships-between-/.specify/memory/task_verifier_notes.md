# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — The submission contains no `data_version.json` (or schema definition) file, nor any description of its fields. Consequently the required schema with `source_url`, `checksum_sha256`, and `timestamp` is missing. The next implementer must create and provide the JSON schema file (or equivalent documentation) containing those three fields.
- **T007b** — declared artifact(s) missing/empty/invalid: src/main.py
- **T008** — declared artifact(s) missing/empty/invalid: src/data/utils.py
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The required artifact `tests/integration/test_data.py` does not exist, so no integration test is present to verify end‑to‑end fetching and descriptor calculation. The task cannot be considered fulfilled until this file is created with a functional test.
- **T013** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/process.py
