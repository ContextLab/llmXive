# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `data/raw/sra_fastq/` directory is empty and `data/checksums/checksums.txt` contains no entries for any FASTQ files. No test verifies that `download_sra_fastq` actually creates `.fastq.gz` files or records their checksums, so the required download artifact is missing.
- **T003** — Requested task execution failed; rerun successfully: code/curate.py exit=1
