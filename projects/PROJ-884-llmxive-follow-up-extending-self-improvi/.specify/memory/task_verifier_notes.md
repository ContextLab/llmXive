# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The integration test `tests/integration/test_checksums.py` fails: the checksum for `data/processed/experiment.log` in the generated `data/checksums.json` does not match the file’s actual SHA‑256 hash, showing the manifest is incorrect. The required behavior—accurate SHA‑256 checksums for every file under `data/`—is therefore not satisfied. Fix the `compute_checksums` implementation (or the file contents) so that the manifest hashes match the real files and the test passes.
- **T021** — declared artifact(s) missing/empty/invalid: data/provenance/seeds.json, tests/unit/test_seed_pin.py
