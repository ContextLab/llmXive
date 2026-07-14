# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T059** — The provided `download_datasets.py` contains only dataset configuration with placeholder checksums and a partially shown `DownloadResult` class; there is no implemented function that downloads a file, computes its checksum, compares it to the expected value, or aborts processing on mismatch. The expected checksum fields are dummy values (“d41d8cd98f00b204e9800998ecf8427e”) and are not used in any verification logic, so the task requirement of checksum‑based integrity checking is not met.
