# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The loader, JSON data, and passing pytest log are genuine and satisfy the schema/fail-loudly requirements, but the checksum file `data/raw/nist_refs.json.sha256` records `5d5e9c2c...` while the collector-computed SHA256 of the actual `nist_refs.json` is `c4adf14483cd33b298ab52f355528663a4ba39b3efc1b00c2e6fb7629eea9c29` — the recorded checksum is fabricated/incorrect. Fix by regenerating the `.sha256` file (e.g. `sha256sum data/raw/nist_refs.json > data/raw/nist_refs.json.sha256`) so it matches the real file.
- **T002** — Requested task execution failed; rerun successfully: code/tests/test_simulation.py exit=2
