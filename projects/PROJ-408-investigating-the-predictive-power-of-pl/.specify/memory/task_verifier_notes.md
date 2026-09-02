# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T039** — The `code/data_loader.py` contains a `_validate_species_mapping` function that performs the required 1:1 checks, but the essential `data/raw/species_list.txt` file is absent, so the validation cannot actually be run. Additionally, the snippet does not show the function being called before any data fetches, leaving the integration unverified. The missing species list file must be provided and the validation invoked in the pipeline for the task to be complete.
- **T042** — The `scripts/audit_data.py` file exists but is truncated and relies on `data/raw/species_list.txt`, which is missing, so the script cannot run. Moreover, the required output `output/reports/retention_audit.txt` was not generated. The task’s essential artifacts are absent, so the requirement is not satisfied.
