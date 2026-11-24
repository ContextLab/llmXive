# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `data/raw/nist_refs.json.sha256` file records a hash that does **not** match the actual contents of `nist_refs.json` (computed hash = a81b3f2b…, recorded = 6c9f020e…). Consequently `load_refs()` raises a checksum‑mismatch error, causing the `test_load_valid` and `test_checksum_matches` unit tests to fail. Moreover, `loader.py` raises a `FileNotFoundError` when a temporary JSON file lacks a `.sha256` file, contradicting the `test_malformed_schema` expectation that checksum verification be skipped. Fix the checksum file and adjust the loader’s checksum logic (or test expectations) so that al
- **T002** — Requested task execution failed; rerun successfully: code/tests/test_simulation.py exit=1
