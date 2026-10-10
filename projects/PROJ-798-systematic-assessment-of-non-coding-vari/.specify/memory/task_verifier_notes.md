# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories exist, but `data/results/structure_manifest.txt` does not list the specified project layout (e.g., `code/data_ingestion`, `data/raw`, `tests/unit`, etc.). The manifest only contains the virtual‑environment paths, so it fails the “list every required directory” check.
- **T002** — The repository does not contain the required `.gitignore` file (or its contents are not shown), and there is no evidence that the specified `git check-ignore` commands were run and produced the expected exit codes. Additionally, the files referenced in the verification steps (`data/raw/snps_raw.vcf.gz` and `data/raw/source_log.txt`) are missing, preventing any real ignore‑rule testing.
- **T004** — Requested task execution failed; rerun successfully: code/data_ingestion/fetch_dbsnp.py exit=1
