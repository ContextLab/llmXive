# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T050** — The provided `code/main.py` only writes a placeholder `results_summary.csv` containing column headers and does not run the full data‑download, preprocessing, model generation, or RSA analysis steps, nor does it produce any intermediate artifacts required by the end‑to‑end pipeline. Consequently the final CSV lacks the computed values the specification expects, and the pipeline is not truly executed from raw data.
- **T051** — The provided `manifest.json` contains the dataset URLs, commit hash, and software versions, but the `checksums` field is empty instead of listing the required checksum values for the repository files. Consequently the manifest does not fulfill the “all checksum values” part of the task.
