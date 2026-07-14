# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T059** — The file defines `compute_file_checksum`, `validate_checksum`, and a checksum cache path, but the shown code never uses these functions to verify a downloaded file against an expected checksum before further processing. The implementation of loading the expected checksums and applying `validate_checksum` in the download workflow is missing (the file is truncated before any such logic). The task requires actual verification logic integrated into the download process, which is not present.
