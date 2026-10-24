# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The CSV file `data/raw/lipophilicity.csv` exists and its SHA‑256 hash matches the value recorded, and the download script ran successfully. However, `data/checksums.txt` does not follow the required format – it contains a line `a7c1b1800dd4673dd264410d814bc952ae14d94b114f85047f09fb2a1603232c  data/raw/lipophilicity.csv` instead of the specified `lipophilicity.csv <checksum>` (filename first, no path). The checksum manifest must be corrected to meet the task specification.
- **T001b** — Requested task execution failed; rerun successfully: code/00_checksum_verify.py exit=1
