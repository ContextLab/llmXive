# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/sieve.py` and `data/raw/mobius_array.npy` artifacts exist and compute the Möbius array, but the required supporting files for the unit tests are missing: the packed array `data/raw/mobius_2bit.npy` is not present in the evidence, and the checksum manifest `data/checksums/manifest.sha256` (which must contain an entry for the packed file) is also absent. Without these files the tests `test_pack_unpack_full_array` and `test_checksum_manifest_contains_packed_file` cannot succeed. Adding the packed file and a correct manifest will satisfy the task.
- **T003** — The repository contains `code/pack.py` and the test suite, but the required data files `data/raw/mobius_array.npy` and `data/raw/mobius_2bit.npy` are missing, causing the round‑trip tests to error. Consequently the checksum manifest cannot be verified against real files, so the task’s core deliverables are not present.
- **T004** — declared artifact(s) missing/empty/invalid: data/processed/window_index.csv, code/window.py
- **T005** — Requested task execution failed; rerun successfully: code/demo_autocorr.py exit=1
