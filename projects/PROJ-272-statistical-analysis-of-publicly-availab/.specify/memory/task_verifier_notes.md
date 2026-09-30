# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001d** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T012b** — The required output file `data/results/raw_record_count.json` does not exist, and the provided `code/ingestion.py` excerpt shows no implementation of a function that counts raw records and writes the JSON with the specified schema. Consequently the task’s core requirement is unmet.
- **T014** — The provided `code/ingestion.py` snippet does not show any implementation of record filtering (label null or text length < 50 words) nor logging of excluded records to `data/interim/exclusions.log`. Moreover, the `exclusions.log` file is missing entirely. The required filtering logic and log artifact are therefore absent.
- **T016** — declared artifact(s) missing/empty/invalid: data/interim/cleaned_adress.csv
