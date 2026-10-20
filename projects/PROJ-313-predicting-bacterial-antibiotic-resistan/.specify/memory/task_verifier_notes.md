# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `data/raw/ncbi_parquet/isolates.parquet` (present) and `src/pipeline/download.py` execution log (exits 0, but both FASTA downloads failed, leaving `data/raw/assemblies/` empty) and the sample‑size CSVs (the script writes `results/sample_sizes.csv`, while the task requires a correctly‑formatted `data/processed/sample_sizes.csv`). The required FASTA files are missing and the sample‑size table is not in the specified location/format.
- **T002** — Requested task execution failed; rerun successfully: src/pipeline/extract_baseline.py exit=1
