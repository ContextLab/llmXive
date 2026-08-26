# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — No ingestion script, output CSV, logs, or analysis results were provided; the claim lacks any tangible artifacts (code, data files, or result tables) required to demonstrate that SRA data were searched, filtered, validated, and that downstream correlation and modeling steps were performed. The implementer must supply the actual scripts and generated output files to satisfy the user stories.
- **T001** — No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`) actually exist; without such artifacts the claim cannot be verified.
- **T039** — No linting or formatting artifacts (e.g., ruff output logs, black diff reports, or updated, clean code files) are present to demonstrate that ruff checks were run and all issues were fixed. The required evidence of the codebase being lint‑checked and black‑formatted is missing.
- **T001a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008a** — No `.env` template file was provided in the evidence; there is no file containing placeholders for `SRA_TOKEN` and `DATA_SOURCE_URL`, so the required artifact is missing.
- **T011a** — No code, script, or fetched data files are provided to demonstrate that the pre‑processed OTU table and serology metadata for the SRP accession series have been retrieved; the required artifact (a data ingestion implementation and its output) is missing.
- **T019a** — No code, notebook, script, or data file was provided that performs or demonstrates conversion of the OTU table to relative abundances, nor any output showing the normalized values. The required artifact for task T019a is missing.
