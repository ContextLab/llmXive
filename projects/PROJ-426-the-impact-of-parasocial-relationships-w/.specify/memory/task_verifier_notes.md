# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — The manifest `data/artifact_manifest.yaml` only lists checksums for the placeholder `.gitkeep` files, while the task requires checksums for *every* raw and derived data artifact; no real data files are present and the unit tests fail because expected files (e.g., `data/raw/file2.csv`) are missing. Consequently the checksum generation does not cover the required artifacts, and the verification step cannot be meaningfully applied.
