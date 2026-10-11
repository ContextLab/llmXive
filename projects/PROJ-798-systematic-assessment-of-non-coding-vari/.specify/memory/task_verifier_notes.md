# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The required `.gitignore` file at the repository (project) root is not present in the collected evidence at all — no artifact entry exists for it. Without the file, the required exclusion patterns cannot be verified, and the `git check-ignore` verification commands (exit 0 for `data/raw/snps_raw.vcf.gz`, exit 1 for `data/raw/source_log.txt`) cannot pass; the implementer must create `.gitignore` with the exact five specified patterns.
- **T004** — Requested task execution failed; rerun successfully: code/data_ingestion/fetch_dbsnp.py exit=1
