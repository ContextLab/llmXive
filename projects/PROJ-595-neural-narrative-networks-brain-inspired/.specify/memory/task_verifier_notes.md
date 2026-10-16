# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The module exists and `compute_sha256` works, but the recorded pytest run for this task failed (2 failed, 12 passed, exit 1): `test_state_file_roundtrip` exposes a real bug where `update_state_file` double-nests the `checksums` key (`{'data/raw': {'checksums': {'checksums': {...}}}}`), and `test_write_manifest_and_verify` fails with `NameError: tmp_path` (a broken test). Fix `update_state_file`'s merge logic and the test, then re-run to green.
