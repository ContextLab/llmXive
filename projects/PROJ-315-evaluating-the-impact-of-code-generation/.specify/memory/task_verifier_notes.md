# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — The provided `code/data/preprocess.py` does not contain logic to generate a random sample of classified PRs nor to write `docs/reports/audit_sample.csv`; it is truncated, contains a typo (`return resul`), and the required CSV file is missing. The task’s core output is therefore not present.
- **T017b** — The `code/data/preprocess.py` file does not implement the required logic to create a CSV with PR ID, commit message, and code snippet, and it contains a bug (`return resul`). Moreover, the expected output file `docs/reports/audit_sample_labeled.csv` is missing entirely.
- **T017c** — The provided `code/data/preprocess.py` is truncated, contains a typo (`return resul`) and never writes the accuracy result to `docs/reports/audit_accuracy.json`. Moreover, the required input file `docs/reports/audit_sample_labeled.csv` and the expected output file `docs/reports/audit_accuracy.json` are absent from the repository. The task’s core artifacts are missing or non‑functional.
