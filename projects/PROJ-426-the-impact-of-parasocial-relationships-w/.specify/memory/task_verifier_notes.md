# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — The manifest `data/artifact_manifest.yaml` only lists the four `.gitkeep` placeholder files and contains no entries for the real raw, processed, or results artifacts that the pipeline should generate. The unit test `test_gather_and_write_manifest` fails because it expects a file `data/raw/file2.csv` that is not present in the manifest, showing the checksum script did not compute hashes for actual data artifacts. To satisfy the task, the script must walk the entire `data` tree, compute SHA‑256 hashes for every real artifact, write them to the manifest, and the verification step must detect any
- **T003** — Requested task execution failed; rerun successfully: code/src/main.py exit=1
- **T010** — Requested task execution failed; rerun successfully: code/src/features/integrate_features.py exit=1
