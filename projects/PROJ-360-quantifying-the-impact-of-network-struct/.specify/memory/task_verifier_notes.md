# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — The `data/raw/cif/` directory contains only 5 CIF files (log shows `--limit 5`), far fewer than the required ≥50 and the script does not query the Materials Project API but downloads a public zip archive instead. Moreover, the metadata entries do not follow the fields the task specifies (the script writes `cif_sha256`/`download_timestamp` but `metadata.yaml` contains `cif_hash`/`timestamp`). These missing/incorrect artifacts mean the task’s requirements are not satisfied.
- **T036a** — Requested task execution failed; rerun successfully: code/download.py exit=1
- **T010** — The provided `code/construct_network.py` contains the required logic (pymatgen parsing, covalent‑radius + tolerance bonding, progressive fallback cut‑offs including 4.0 Å and 4.5 Å, and building a `networkx.Graph`). However, there is no evidence that ≥50 CIF files exist, were processed, and that corresponding graph pickle files (or a manifest) were created, nor do the test logs show a successful run of the script. A passing test and actual output artifacts are needed to satisfy the task.
- **T011** — Requested task execution failed; rerun successfully: code/save_networks.py exit=1
