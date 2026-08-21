# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or command output was provided; there is no evidence that the required folders (`code/`, `tests/`, `data/`, `docs/`, `specs/`) actually exist or that `ls -d …` succeeded with exit code 0. The implementer must supply the filesystem snapshot or command result confirming the structure.
- **T008** — The repository contains `code/utils/checksums.py`, but the required output file `data/.checksums.json` is absent, and there is no evidence that the script actually writes the manifest or performs the verification step. Additionally, the `data/` sub‑directories (`raw/`, `processed/`, `validation/`) are not shown to exist. The task’s core deliverables are therefore missing.
- **T012b** — The repository contains `code/data/download_orca.py`, but the file is truncated and does not show any logic that selects a random subset of 50 clips or writes `data/raw/scenarios.csv`. Moreover, the required output file `data/raw/scenarios.csv` is absent from the disk. Consequently, the task’s core deliverable (a CSV with exactly 50 rows) is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/latents.csv
